"""Automation support metric (general #6)."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricResult


class AutomationSupportMetric(BaseMetric):
    code: ClassVar[str] = "automation_support"
    name: ClassVar[str] = "End-to-End Automation Coverage"
    unit: ClassVar[str] = "ratio"
    higher_is_better: ClassVar[bool] = True

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        # A run is "fully automated" if no manual intervention markers exist.
        markers = run_record.get("metadata", {}).get("manual_interventions", 0)
        ratio = 1.0 if markers == 0 else 0.0
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=ratio,
            unit=self.unit,
            rationale=f"Manual interventions recorded: {markers}",
        )
