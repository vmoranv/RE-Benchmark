"""M5 — Mobile Coverage Score.

Measures the number of Android WebView debugging and APK analysis features
completed out of a standard feature checklist.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M5MobileCoverage(BaseMetric):
    code: ClassVar[str] = "M5"
    name: ClassVar[str] = "Mobile Coverage Score"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.0

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        meta = run_record.get("metadata", {})
        completed = meta.get("mobile_features_completed", 0)
        total = meta.get("mobile_features_total", 0)

        if total == 0:
            return _fallback(run_record, rounds)

        ratio = completed / total
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
            rationale=f"Completed {completed}/{total} mobile debugging features ({ratio:.1%}).",
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
            metric_code="M5",
            value_num=float(ordered[0]["score"]),
            unit="percent",
            grade=MetricGrade.PARTIAL,
            rationale="No mobile feature data; using round score.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M5",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No mobile coverage data.",
    )
