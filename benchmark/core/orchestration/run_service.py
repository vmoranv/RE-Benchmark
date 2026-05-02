"""End-to-end run service.

Orchestrates a single :class:`RunSpec` through the state machine, calls
the configured evaluator, persists state at every transition, runs
metric calculators, and returns a fully populated :class:`RunRecord`.

The service is intentionally synchronous-with-asyncio (``await`` boundaries
only at the IO edges). It does not start a Celery task; that remains the
job of ``apps.worker.tasks.run_pipeline`` which delegates back here once
plumbing is complete.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from benchmark.core.domain import (
    ArtifactKind,
    MetricGrade,
    MetricResult,
    RunRecord,
    RunRoundRecord,
    RunSpec,
    RunState,
)
from benchmark.core.orchestration.state_machine import StateMachine
from benchmark.core.utils.canonical_json import canonicalize_bytes
from benchmark.core.utils.content_hash import sha256_bytes

if TYPE_CHECKING:
    from benchmark.core.abstractions.artifact_store import ArtifactStore
    from benchmark.core.abstractions.dimension import BaseDimension
    from benchmark.core.abstractions.evaluator import BaseEvaluator
    from benchmark.core.abstractions.model_adapter import ModelAdapter
    from benchmark.core.domain import SampleVariant
    from benchmark.core.persistence.repositories.runs import RunRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _grade_str(grade: object) -> str | None:
    """Best-effort coercion of a grade value (enum or str) to its string form."""
    if grade is None:
        return None
    value = getattr(grade, "value", None)
    if isinstance(value, str):
        return value
    if isinstance(grade, str):
        return grade
    return str(grade)


def compute_spec_digest(spec: RunSpec) -> bytes:
    """SHA-256 over the canonical JSON of the spec — Q2 determinism foundation."""
    return sha256_bytes(canonicalize_bytes(spec.model_dump(mode="json")))


class RunService:
    """Drives a run from PLANNED to FINALIZED (or FAILED)."""

    def __init__(
        self,
        *,
        repository: RunRepository,
        artifact_store: ArtifactStore,
        evaluator: BaseEvaluator,
    ) -> None:
        self._repo = repository
        self._artifacts = artifact_store
        self._evaluator = evaluator

    async def submit(self, spec: RunSpec) -> RunRecord:
        """Create the initial RunRecord and persist it in PLANNED state."""
        record = RunRecord(
            id=uuid4(),
            spec_digest=compute_spec_digest(spec),
            spec=spec,
            state=RunState.PLANNED,
            created_at=_utcnow(),
        )
        await self._repo.insert(record)
        return record

    async def execute(
        self,
        run_id: UUID,
        *,
        dimension: BaseDimension,
        sample: SampleVariant,
        model: ModelAdapter,
    ) -> RunRecord:
        """Run the full pipeline. Returns the final record."""

        record = await self._repo.get(run_id)
        if record is None:
            msg = f"run {run_id} not found"
            raise LookupError(msg)
        sm = StateMachine(record.state)

        async def goto(state: RunState, *, error: str | None = None) -> None:
            sm.transition(state)
            await self._repo.update_state(run_id, state, error=error)
            record.state = state
            if error is not None:
                record.error = error

        record.started_at = _utcnow()
        try:
            await goto(RunState.PRECHECK)
            challenges = list(dimension.list_challenges())
            if not challenges:
                await goto(RunState.FAILED, error="dimension has no challenges")
                record.finished_at = _utcnow()
                return record
            challenge = challenges[0]

            prior: list[dict] = []
            round_states = (
                (RunState.R1, RunState.V1, 1),
                (RunState.R2, RunState.V2, 2),
                (RunState.R3, RunState.V3, 3),
            )
            for r_state, v_state, round_no in round_states:
                await goto(r_state)
                round_payload = await self._evaluator.run_round(
                    run_id=run_id,
                    round_no=round_no,
                    challenge=challenge,
                    sample=sample,
                    model=model,
                    prior_rounds=prior,
                )
                round_record = await self._persist_round(run_id, round_no, round_payload)
                if round_payload.get("state") != "SUCCESS":
                    await goto(RunState.FAILED, error=round_payload.get("error"))
                    record.finished_at = _utcnow()
                    return record
                # Carry parsed payload forward so prompts can reference it.
                prior.append(
                    {
                        "round_no": round_no,
                        "grade": round_payload["grade"].value
                        if hasattr(round_payload["grade"], "value")
                        else round_payload["grade"],
                        "score": round_payload["score"],
                        "details": round_payload["details"],
                        "payload": round_payload["parsed"].get("payload"),
                        "obfuscated_code": round_payload["parsed"].get("payload", ""),
                    }
                )
                await goto(v_state)
                _ = round_record

            await goto(RunState.JUDGE)
            judge_payload = await self._evaluator.judge(run_id, prior)
            await self._persist_round(
                run_id,
                99,
                {
                    "state": "SUCCESS",
                    "round_no": 99,
                    "prompt": "<llm-as-judge>",
                    "response_text": judge_payload.get("rationale", ""),
                    "tool_calls": [],
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cache_hit_tokens": 0,
                        "cost_usd": 0.0,
                    },
                    "model_version": None,
                    "parsed": {"readability_score": judge_payload.get("score", 0.0) * 10},
                    "grade": judge_payload.get("grade"),
                    "score": judge_payload.get("score"),
                    "details": {},
                    "latency_ms": 0,
                },
            )

            await goto(RunState.METRICS)
            metric_results = self._compute_metrics(record, dimension)
            record.metadata.setdefault("metric_results", []).extend(
                [m.model_dump(mode="json") for m in metric_results]
            )

            await goto(RunState.FINALIZED)
        except Exception as exc:
            await goto(RunState.FAILED, error=repr(exc))
        finally:
            record.finished_at = _utcnow()
        return record

    async def _persist_round(
        self,
        run_id: UUID,
        round_no: int,
        payload: dict,
    ) -> RunRoundRecord:
        prompt_id = await self._artifacts.put(
            payload["prompt"].encode("utf-8"),
            mime_type="text/plain",
            kind=ArtifactKind.PROMPT.value,
            metadata={"run_id": str(run_id), "round_no": round_no},
        )
        response_id = None
        if payload.get("response_text"):
            response_id = await self._artifacts.put(
                payload["response_text"].encode("utf-8"),
                mime_type="text/plain",
                kind=ArtifactKind.RESPONSE.value,
                metadata={"run_id": str(run_id), "round_no": round_no},
            )

        round_record = RunRoundRecord(
            run_id=run_id,
            round_no=round_no,
            prompt_artifact_id=prompt_id,
            response_artifact_id=response_id,
            input_tokens=payload["usage"].get("input_tokens", 0),
            output_tokens=payload["usage"].get("output_tokens", 0),
            cache_hit_tokens=payload["usage"].get("cache_hit_tokens", 0),
            cost_usd=payload["usage"].get("cost_usd"),
            latency_ms=payload.get("latency_ms"),
            state=payload.get("state", "SUCCESS"),
            error=payload.get("error"),
            started_at=_utcnow(),
            finished_at=_utcnow(),
            metadata={
                "model_version": payload.get("model_version"),
                "grade": _grade_str(payload.get("grade")),
                "score": payload.get("score"),
                "details": payload.get("details", {}),
                "parsed_keys": sorted((payload.get("parsed") or {}).keys()),
            },
        )
        await self._repo.append_round(run_id, round_record)
        return round_record

    def _compute_metrics(self, record: RunRecord, dimension: BaseDimension) -> list[MetricResult]:
        run_dict = record.model_dump(mode="json")
        rounds = []
        for r in record.rounds:
            r_dict = r.model_dump(mode="json")
            r_dict["round_no"] = r.round_no
            r_dict["state"] = r.state
            r_dict["usage"] = {
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cache_hit_tokens": r.cache_hit_tokens,
                "cost_usd": r.cost_usd,
            }
            r_dict["score"] = r.metadata.get("score")
            r_dict["grade"] = r.metadata.get("grade")
            r_dict["details"] = r.metadata.get("details", {})
            r_dict["parsed"] = (
                {"readability_score": (r.metadata.get("score") or 0.0) * 10}
                if r.round_no == 99
                else {}
            )
            rounds.append(r_dict)
        out: list[MetricResult] = []
        for metric in dimension.list_metrics():
            try:
                out.append(metric.compute(run_dict, rounds, artifacts={}))
            except Exception as exc:
                # Don't let one bad metric kill the run.
                out.append(
                    MetricResult(
                        run_id=record.id,
                        metric_code=metric.code,
                        value_num=None,
                        unit=metric.unit,
                        grade=MetricGrade.NOT_APPLICABLE,
                        rationale=f"metric raised {type(exc).__name__}: {exc}",
                    )
                )
        return out
