"""D1 Deobfuscation challenge — restore obfuscated JS to a readable equivalent."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import jinja2

from benchmark.core.abstractions.challenge import BaseChallenge, ChallengeResult
from benchmark.core.domain import MetricGrade, SampleVariant
from benchmark.core.sandbox.node_runner import NodeSubprocessRunner

_PROMPT_DIR = Path(__file__).parent / "prompts"
_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_PROMPT_DIR),
    undefined=jinja2.StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)


_FENCED_JS = re.compile(r"```(?:js|javascript)?\n(.*?)\n```", re.DOTALL)


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    """Cheap textual heuristic used when no semantic suite is attached."""
    score = 0.5
    details: dict[str, float] = {}
    sa_hits = len(re.findall(r"_0x[0-9a-f]{4,}", code, flags=re.IGNORECASE))
    details["string_array_hits"] = sa_hits
    if sa_hits > 5:
        score -= 0.2
    legible_kw = sum(1 for kw in ("function ", "const ", "let ", "return ") if kw in code)
    details["legible_keywords"] = legible_kw
    score += min(0.3, 0.05 * legible_kw)
    obf_size = (sample.metadata or {}).get("obfuscated_size")
    if obf_size:
        ratio = len(code) / max(1, obf_size)
        details["length_ratio"] = ratio
        if 0.2 <= ratio <= 5.0:
            score += 0.1
    return max(0.0, min(1.0, score)), details


class DeobfuscationChallenge(BaseChallenge):
    """Three-round deobfuscation prompt routine.

    R1 — minimal context, ask to deobfuscate.
    R2 — provide objective check failure details, ask to fix.
    R3 — ask to rewrite for human readability.
    """

    code = "D01.deobfuscate"
    rounds = 3
    early_terminate_on_pass = False
    allow_retry = True

    PASS_THRESHOLD = 0.9
    PARTIAL_THRESHOLD = 0.4

    def __init__(
        self,
        *,
        node_runner: NodeSubprocessRunner | None = None,
        export_name: str = "calculateDiscount",
    ) -> None:
        # ``node_runner`` is optional so unit tests can construct the challenge
        # without invoking Node. ``export_name`` is the symbol expected on the
        # candidate's CommonJS exports object — the smoke sample exports
        # ``calculateDiscount`` and dimension-specific subclasses override.
        self._node_runner = node_runner
        self._export_name = export_name

    def build_prompt(
        self,
        sample: SampleVariant,
        round_no: int,
        prior: list[dict],
    ) -> str:
        template_name = f"round{round_no}.j2"
        template = _ENV.get_template(template_name)
        ctx = {
            "sample": sample,
            "prior": prior,
            "obfuscated_code_inline": (
                prior[-1]["obfuscated_code"] if prior else "{{OBFUSCATED_CODE}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        # Look for fenced JS block first; fall back to whole response.
        match = _FENCED_JS.search(response)
        code = match.group(1) if match else response.strip()
        return {
            "ok": bool(code),
            "round_no": round_no,
            "payload": code,
        }

    def objective_check(
        self,
        parsed: dict,
        sample: SampleVariant,
    ) -> ChallengeResult:
        if not parsed["ok"] or not parsed["payload"]:
            return ChallengeResult(
                grade=MetricGrade.FAIL,
                score=0.0,
                rationale="Empty or unparseable response.",
            )
        code = parsed["payload"]
        test_cases = list((sample.metadata or {}).get("semantic_test_cases", []))

        # Sandbox-driven path.
        if test_cases and self._node_runner is not None:
            export_name = (sample.metadata or {}).get("export_name", self._export_name)
            try:
                result = asyncio.run(
                    self._node_runner.run(
                        candidate_code=code,
                        export_name=export_name,
                        test_cases=test_cases,
                    )
                )
            except RuntimeError:
                # Already inside an event loop (e.g. inside the API request
                # handler). Fall back to running on a fresh loop in a thread.
                result = _run_in_new_loop(
                    self._node_runner.run(
                        candidate_code=code,
                        export_name=export_name,
                        test_cases=test_cases,
                    )
                )
            ratio = result.pass_ratio
            if ratio >= self.PASS_THRESHOLD:
                grade = MetricGrade.PASS
            elif ratio >= self.PARTIAL_THRESHOLD:
                grade = MetricGrade.PARTIAL
            else:
                grade = MetricGrade.FAIL
            return ChallengeResult(
                grade=grade,
                score=ratio,
                details={
                    "sandbox_test_summary": result.to_dict(),
                    "string_array_hits": len(
                        re.findall(r"_0x[0-9a-f]{4,}", code, flags=re.IGNORECASE)
                    ),
                },
                rationale=(
                    f"Sandbox executed {result.total} test case(s); "
                    f"{result.passed} passed (ratio={ratio:.3f})."
                ),
            )

        # Heuristic baseline for unit tests / samples without a suite.
        score, details = _heuristic_score(code, sample)
        if score >= 0.75:
            grade = MetricGrade.PASS
        elif score >= self.PARTIAL_THRESHOLD:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL
        return ChallengeResult(
            grade=grade,
            score=score,
            details=details,
            rationale=(
                "Heuristic fallback used because no Node runner was provided "
                "or the sample carries no semantic_test_cases."
            ),
        )


def _run_in_new_loop(coro):
    """Run ``coro`` on a fresh event loop, even if one is already running."""
    import threading

    result_holder: dict[str, object] = {}

    def _target() -> None:
        loop = asyncio.new_event_loop()
        try:
            result_holder["value"] = loop.run_until_complete(coro)
        except Exception as exc:
            result_holder["error"] = exc
        finally:
            loop.close()

    th = threading.Thread(target=_target, daemon=True)
    th.start()
    th.join()
    if "error" in result_holder:
        raise result_holder["error"]  # type: ignore[misc]
    return result_holder["value"]
