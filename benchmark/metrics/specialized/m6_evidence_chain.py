"""M6 — Evidence Chain Completeness.

Measures the proportion of conclusions that have traceable evidence back to
raw data sources via evidenceId → sourceEventId links.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M6EvidenceChain(BaseMetric):
    code: ClassVar[str] = "M6"
    name: ClassVar[str] = "Evidence Chain Completeness"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.5

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        total_conclusions = 0
        traced = 0
        for r in rounds:
            details = r.get("details", {})
            conclusions = details.get("conclusions", [])
            if not conclusions:
                continue
            total_conclusions += len(conclusions)
            traced += sum(
                1 for c in conclusions if c.get("evidence_id") and c.get("source_event_id")
            )

        if total_conclusions == 0:
            return _fallback(run_record, rounds)

        ratio = traced / total_conclusions
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
            rationale=f"{traced}/{total_conclusions} conclusions have traceable evidence ({ratio:.1%}).",
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
            metric_code="M6",
            value_num=float(ordered[0]["score"]),
            unit="percent",
            grade=MetricGrade.PARTIAL,
            rationale="No evidence chain data; using round score.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M6",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No evidence chain data.",
    )
