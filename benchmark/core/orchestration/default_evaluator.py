"""Default 3-round evaluator implementation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from benchmark.core.abstractions.evaluator import BaseEvaluator
from benchmark.core.abstractions.model_adapter import ChatRequest

if TYPE_CHECKING:
    from uuid import UUID

    from benchmark.core.abstractions.challenge import BaseChallenge
    from benchmark.core.abstractions.model_adapter import ModelAdapter
    from benchmark.core.domain import SampleVariant


class DefaultEvaluator(BaseEvaluator):
    """Standard evaluator: build prompt → call model → parse → verify.

    Persistence is delegated to a separate writer (``RunRoundRepository``)
    in production; here we return all data in dicts for the caller to
    persist atomically.
    """

    async def run_round(
        self,
        run_id: UUID,
        round_no: int,
        challenge: BaseChallenge,
        sample: SampleVariant,
        *,
        model: ModelAdapter,
        prior_rounds: list[dict],
    ) -> dict:
        prompt = challenge.build_prompt(sample, round_no, prior_rounds)
        messages = [{"role": "user", "content": prompt}]

        t0 = time.monotonic()
        try:
            resp = await model.send(
                ChatRequest(messages=messages, max_tokens=4096, temperature=0.0)
            )
        except Exception as exc:
            return {
                "state": "FAILED",
                "round_no": round_no,
                "error": repr(exc),
                "prompt": prompt,
            }
        latency_ms = int((time.monotonic() - t0) * 1000)

        parsed = challenge.parse_response(resp["content"], round_no)
        verification = challenge.objective_check(parsed, sample)

        return {
            "state": "SUCCESS",
            "round_no": round_no,
            "prompt": prompt,
            "response_text": resp["content"],
            "tool_calls": resp.get("tool_calls", []),
            "usage": resp["usage"],
            "model_version": resp.get("model_version"),
            "parsed": parsed,
            "grade": verification.grade,
            "score": verification.score,
            "details": verification.details,
            "latency_ms": latency_ms,
        }

    async def judge(self, run_id: UUID, all_rounds: list[dict]) -> dict:
        """Stub judge that aggregates objective grades.

        A production judge calls a separate LLM with a rubric prompt; this
        baseline returns the best round's grade so the pipeline is end-to-
        end runnable without an extra model dependency.
        """

        if not all_rounds:
            return {"grade": "fail", "score": 0.0, "rationale": "no rounds completed"}
        best = max(all_rounds, key=lambda r: r.get("score", 0.0))
        return {
            "grade": best.get("grade", "fail"),
            "score": best.get("score", 0.0),
            "rationale": "baseline judge: highest objective score wins",
        }
