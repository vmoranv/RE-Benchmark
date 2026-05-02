"""D18 — LLM Semantic Understanding Depth Probing challenge."""

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

OBFUSCATION_LEVELS = {"L1", "L2", "L3", "L4", "L5"}


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float] = {}

    understanding_keywords = [
        "semantic",
        "behavior",
        "intent",
        "purpose",
        "function",
        "logic",
        "algorithm",
        "flow",
        "control flow",
        "data flow",
    ]
    reasoning_keywords = [
        "because",
        "therefore",
        "since",
        "due to",
        "reason",
        "analysis",
        "inference",
        "conclusion",
        "hypothesis",
    ]
    correctness_keywords = [
        "correct",
        "equivalent",
        "preserves",
        "matches",
        "identical",
        "same output",
        "consistent",
    ]

    understanding_hits = sum(1 for kw in understanding_keywords if kw in code.lower())
    reasoning_hits = sum(1 for kw in reasoning_keywords if kw in code.lower())
    correctness_hits = sum(1 for kw in correctness_keywords if kw in code.lower())

    details["understanding_keyword_hits"] = understanding_hits
    details["reasoning_keyword_hits"] = reasoning_hits
    details["correctness_keyword_hits"] = correctness_hits

    score += min(0.15, 0.03 * understanding_hits)
    score += min(0.15, 0.03 * reasoning_hits)
    score += min(0.15, 0.03 * correctness_hits)

    obf_level = (sample.metadata or {}).get("obfuscation_level", "")
    level_map = {"L1": 0.20, "L2": 0.15, "L3": 0.10, "L4": 0.05, "L5": 0.00}
    level_bonus = level_map.get(obf_level, 0.0)
    details["obfuscation_level_bonus"] = level_bonus
    score += level_bonus

    legible_kw = sum(1 for kw in ("function ", "const ", "let ", "return ", "class ") if kw in code)
    details["legible_keyword_count"] = legible_kw
    score += min(0.10, 0.02 * legible_kw)

    return max(0.0, min(1.0, score)), details


class LLMSemanticDepthChallenge(BaseChallenge):
    """Three-round LLM semantic understanding depth probing challenge.

    Uses structured obfuscation at levels L1-L5 as probes to determine whether
    the LLM truly understands code semantics vs relies on pattern matching.

    R1 — Present obfuscated code at a specific level, ask for semantic explanation
         and deobfuscated equivalent.
    R2 — Provide feedback, ask to refine analysis with deeper reasoning.
    R3 — Ask for complete final analysis with decay curve assessment.
    """

    code = "D18.llm_semantic_depth"
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
        expected_semantics = list((sample.metadata or {}).get("expected_semantic_properties", []))

        if expected_semantics:
            matched = sum(1 for prop in expected_semantics if prop.lower() in code.lower())
            ratio = matched / max(1, len(expected_semantics))
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
                    "expected_semantic_properties": len(expected_semantics),
                    "matched_properties": matched,
                    "obfuscation_level": (sample.metadata or {}).get(
                        "obfuscation_level", "unknown"
                    ),
                },
                rationale=(
                    f"Matched {matched}/{len(expected_semantics)} semantic properties "
                    f"at obfuscation level {(sample.metadata or {}).get('obfuscation_level', 'unknown')} "
                    f"(ratio={ratio:.3f})."
                ),
            )

        score, details = _heuristic_score(code, sample)
        details["obfuscation_level"] = (sample.metadata or {}).get("obfuscation_level", "unknown")
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
