"""M7 — Protocol Recovery Automation Rate.

Measures the proportion of raw traffic that is automatically converted to
readable protocol definitions without human intervention.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M7ProtocolAutomation(BaseMetric):
    code: ClassVar[str] = "M7"
    name: ClassVar[str] = "Protocol Recovery Automation Rate"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.5

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        meta = run_record.get("metadata", {})
        auto_fields = meta.get("protocol_fields_auto_recovered", 0)
        total_fields = meta.get("protocol_fields_total", 0)

        if total_fields == 0:
            return _fallback(run_record, rounds)

        ratio = auto_fields / total_fields
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
            rationale=f"Auto-recovered {auto_fields}/{total_fields} protocol fields ({ratio:.1%}).",
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
            metric_code="M7",
            value_num=float(ordered[0]["score"]),
            unit="percent",
            grade=MetricGrade.PARTIAL,
            rationale="No protocol field data; using round score.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M7",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No protocol recovery data.",
    )
