"""Complexity reduction metric (general #5)."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricResult


class ComplexityReductionMetric(BaseMetric):
    code: ClassVar[str] = "complexity_reduction"
    name: ClassVar[str] = "Cyclomatic Complexity Reduction"
    unit: ClassVar[str] = "delta"
    higher_is_better: ClassVar[bool] = True

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        before = run_record.get("metadata", {}).get("complexity_before")
        after = run_record.get("metadata", {}).get("complexity_after")
        if before is None or after is None:
            return MetricResult(
                run_id=run_record["id"],
                metric_code=self.code,
                value_num=None,
                unit=self.unit,
                rationale="complexity_before/after metadata missing; metric not applicable.",
            )
        delta = before - after
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=delta,
            unit=self.unit,
            value_json={"before": before, "after": after, "delta": delta},
            rationale=f"Reduced cyclomatic complexity by {delta} units.",
        )
