"""D17 — Obfuscator Correctness Verification challenge."""

from __future__ import annotations

import re
from pathlib import Path

import jinja2

from benchmark.core.abstractions.challenge import BaseChallenge, ChallengeResult
from benchmark.core.domain import MetricGrade, SampleVariant

_PROMPT_DIR = Path(__file__).parent / "prompts"
_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_PROMPT_DIR),
    undefined=jinja2.StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)

_FENCED_JS = re.compile(r"```(?:js|javascript)?\n(.*?)\n```", re.DOTALL)


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float] = {}

    semantic_keywords = ["semantic", "equivalent", "equivalence", "preserves", "behavior"]
    test_keywords = ["test", "assert", "assertion", "expect", "verify", "validate"]
    diff_keywords = ["diff", "compare", "comparison", "match", "mismatch", "diverge"]

    semantic_hits = sum(1 for kw in semantic_keywords if kw in code.lower())
    test_hits = sum(1 for kw in test_keywords if kw in code.lower())
    diff_hits = sum(1 for kw in diff_keywords if kw in code.lower())

    details["semantic_keyword_hits"] = semantic_hits
    details["test_keyword_hits"] = test_hits
    details["diff_keyword_hits"] = diff_hits

    score += min(0.20, 0.05 * semantic_hits)
    score += min(0.15, 0.05 * test_hits)
    score += min(0.15, 0.05 * diff_hits)

    has_test_case = bool(re.search(r"(assert|expect|console\.log|toEqual|toBe|deepEqual)", code))
    has_function_compare = bool(
        re.search(r"(original|obfuscated|compare|output|result)", code.lower())
    )

    details["has_test_case_pattern"] = float(has_test_case)
    details["has_comparison_pattern"] = float(has_function_compare)

    if has_test_case:
        score += 0.10
    if has_function_compare:
        score += 0.10

    return max(0.0, min(1.0, score)), details


class ObfuscatorCorrectnessChallenge(BaseChallenge):
    """Three-round obfuscator correctness verification challenge.

    R1 — Present original + obfuscated code, ask to verify semantic equivalence.
    R2 — Provide feedback on gaps, ask to fix verification approach.
    R3 — Ask for complete final verification output.
    """

    code = "D17.obfuscator_correctness"
    rounds = 3
    early_terminate_on_pass = False
    allow_retry = True

    PASS_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.40

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
        expected_properties = list((sample.metadata or {}).get("expected_semantic_properties", []))

        if expected_properties:
            matched = sum(1 for prop in expected_properties if prop.lower() in code.lower())
            ratio = matched / max(1, len(expected_properties))
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
                    "expected_properties": len(expected_properties),
                    "matched_properties": matched,
                },
                rationale=(
                    f"Matched {matched}/{len(expected_properties)} semantic "
                    f"properties (ratio={ratio:.3f})."
                ),
            )

        score, details = _heuristic_score(code, sample)
        if score >= 0.70:
            grade = MetricGrade.PASS
        elif score >= self.PARTIAL_THRESHOLD:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL
        return ChallengeResult(
            grade=grade,
            score=score,
            details=details,
            rationale="Heuristic fallback used; no expected_semantic_properties in sample metadata.",
        )
