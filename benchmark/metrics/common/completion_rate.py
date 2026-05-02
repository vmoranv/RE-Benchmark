"""3-round Prompt completion rate (general metric #1)."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class CompletionRateMetric(BaseMetric):
    code: ClassVar[str] = "completion_rate"
    name: ClassVar[str] = "3-Round Prompt Completion Rate"
    unit: ClassVar[str] = "ratio"
    higher_is_better: ClassVar[bool] = True

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        completed = sum(1 for r in rounds if r.get("state") == "SUCCESS")
        total = max(1, len([r for r in rounds if r.get("round_no", 0) in (1, 2, 3)]))
        ratio = completed / total
        if ratio >= 1.0:
            grade = MetricGrade.PASS
        elif ratio > 0.0:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=ratio,
            unit=self.unit,
            grade=grade,
            rationale=f"{completed}/{total} rounds completed",
        )
