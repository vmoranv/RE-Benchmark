"""M8 — Semantic Fidelity for deobfuscation outputs."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


def _find_sandbox_ratio(rounds: list[dict]) -> tuple[float | None, dict | None]:
    """Find the latest sandbox-reported pass_ratio from evaluation rounds."""
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    for r in ordered:
        summary = r.get("details", {}).get("sandbox_test_summary")
        if summary and summary.get("pass_ratio") is not None:
            return summary["pass_ratio"], summary
    return None, None


def _fallback_score(rounds: list[dict]) -> float | None:
    """Return objective_check score from latest round, or None."""
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    if ordered and ordered[0].get("score") is not None:
        return float(ordered[0]["score"])
    return None


class M8SemanticFidelity(BaseMetric):
    code: ClassVar[str] = "M8"
    name: ClassVar[str] = "Obfuscation Semantic Fidelity"
    unit: ClassVar[str] = "pass_ratio"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 2.0

    PASS_THRESHOLD = 0.9

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        suite_id = run_record.get("metadata", {}).get("semantic_test_suite_id") or run_record.get(
            "config", {}
        ).get("metadata", {}).get("semantic_test_suite_id")
        if not suite_id:
            return MetricResult(
                run_id=run_record["id"],
                metric_code=self.code,
                value_num=None,
                unit=self.unit,
                grade=MetricGrade.NOT_APPLICABLE,
                rationale="No semantic_test_suite_id attached to sample.",
            )

        ratio, summary = _find_sandbox_ratio(rounds)
        if ratio is not None and summary is not None:
            grade = MetricGrade.PASS if ratio >= self.PASS_THRESHOLD else MetricGrade.PARTIAL
            return MetricResult(
                run_id=run_record["id"],
                metric_code=self.code,
                value_num=ratio,
                unit=self.unit,
                grade=grade,
                value_json=summary,
                rationale=(
                    f"{summary.get('passed', 0)}/{summary.get('total', 0)} test cases passed."
                ),
            )

        fallback = _fallback_score(rounds)
        if fallback is not None:
            return MetricResult(
                run_id=run_record["id"],
                metric_code=self.code,
                value_num=fallback,
                unit=self.unit,
                grade=MetricGrade.PARTIAL,
                rationale="No sandbox suite output; using objective_check heuristic score.",
            )
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=0.0,
            unit=self.unit,
            grade=MetricGrade.FAIL,
            rationale="No successful rounds to evaluate.",
        )
