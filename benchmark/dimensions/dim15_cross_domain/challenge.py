"""D15 — Cross-Domain Evidence Correlation challenge."""

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

_FENCED_BLOCK = re.compile(r"```(?:json|text)?\n(.*?)\n```", re.DOTALL)


def _heuristic_score(text: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float] = {}
    causal_keywords = ["causal", "causes", "caused by", "leads to", "triggers", "results in"]
    evidence_keywords = ["evidence", "correlation", "linked", "linked to", "connects"]
    chain_keywords = ["chain", "sequence", "flow", "path", "timeline"]

    causal_hits = sum(1 for kw in causal_keywords if kw in text.lower())
    evidence_hits = sum(1 for kw in evidence_keywords if kw in text.lower())
    chain_hits = sum(1 for kw in chain_keywords if kw in text.lower())

    details["causal_keyword_hits"] = causal_hits
    details["evidence_keyword_hits"] = evidence_hits
    details["chain_keyword_hits"] = chain_hits

    score += min(0.25, 0.05 * causal_hits)
    score += min(0.20, 0.05 * evidence_hits)
    score += min(0.15, 0.05 * chain_hits)

    edge_patterns = re.findall(r"->|→|⇒|causes|leads to", text)
    details["edge_notation_count"] = len(edge_patterns)
    if edge_patterns:
        score += min(0.10, 0.02 * len(edge_patterns))

    return max(0.0, min(1.0, score)), details


class CrossDomainChallenge(BaseChallenge):
    """Three-round cross-domain evidence correlation challenge.

    R1 — Present multi-source evidence, ask for causal chain analysis.
    R2 — Provide feedback, ask to fix gaps in correlation.
    R3 — Ask for complete final causal graph.
    """

    code = "D15.cross_domain"
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
                prior[-1]["obfuscated_code"] if prior else "{{MULTI_SOURCE_EVIDENCE}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        match = _FENCED_BLOCK.search(response)
        payload = match.group(1) if match else response.strip()
        return {
            "ok": bool(payload),
            "round_no": round_no,
            "payload": payload,
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

        text = parsed["payload"]
        expected_edges = list((sample.metadata or {}).get("expected_causal_edges", []))

        if expected_edges:
            matched = sum(
                1
                for edge in expected_edges
                if edge["source"].lower() in text.lower() and edge["target"].lower() in text.lower()
            )
            ratio = matched / max(1, len(expected_edges))
            if ratio >= self.PASS_THRESHOLD:
                grade = MetricGrade.PASS
            elif ratio >= self.PARTIAL_THRESHOLD:
                grade = MetricGrade.PARTIAL
            else:
                grade = MetricGrade.FAIL
            return ChallengeResult(
                grade=grade,
                score=ratio,
                details={"expected_edges": len(expected_edges), "matched_edges": matched},
                rationale=(
                    f"Matched {matched}/{len(expected_edges)} expected causal edges "
                    f"(ratio={ratio:.3f})."
                ),
            )

        score, details = _heuristic_score(text, sample)
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
            rationale="Heuristic fallback used; no expected_causal_edges in sample metadata.",
        )
