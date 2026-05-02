"""M3 — Cross-Domain Correlation Accuracy.

Measures the proportion of correct causal links produced by the model when
given multi-source evidence (network, memory, hook, syscall, binary symbols).
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M3CrossDomainAccuracy(BaseMetric):
    code: ClassVar[str] = "M3"
    name: ClassVar[str] = "Cross-Domain Correlation Accuracy"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.5

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        expected_edges = 0
        correct_edges = 0
        for r in rounds:
            details = r.get("details", {})
            edges = details.get("causal_edges", [])
            if not edges:
                continue
            expected_edges += len(edges)
            correct_edges += sum(1 for e in edges if e.get("correct"))

        if expected_edges == 0:
            return _fallback(run_record, rounds)

        ratio = correct_edges / expected_edges
        grade = (
            MetricGrade.PASS
            if ratio >= 0.8
            else MetricGrade.PARTIAL
            if ratio >= 0.4
            else MetricGrade.FAIL
        )
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=ratio,
            unit=self.unit,
            grade=grade,
            rationale=f"{correct_edges}/{expected_edges} causal edges correctly identified ({ratio:.1%}).",
        )


def _fallback(run_record: dict, rounds: list[dict]) -> MetricResult:
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    if ordered and ordered[0].get("score") is not None:
        return MetricResult(
            run_id=run_record["id"],
            metric_code="M3",
            value_num=float(ordered[0]["score"]),
            unit="percent",
            grade=MetricGrade.PARTIAL,
            rationale="No edge data; using round score.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M3",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No cross-domain correlation data.",
    )
