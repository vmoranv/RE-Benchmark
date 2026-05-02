"""Correctness metric (general #3)."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class CorrectnessMetric(BaseMetric):
    code: ClassVar[str] = "correctness"
    name: ClassVar[str] = "Execution Correctness"
    unit: ClassVar[str] = "ratio"
    higher_is_better: ClassVar[bool] = True

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        passes = sum(1 for r in rounds if r.get("grade") == MetricGrade.PASS.value)
        total = len([r for r in rounds if r.get("round_no", 0) in (1, 2, 3)])
        ratio = passes / total if total else 0.0
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=ratio,
            unit=self.unit,
            grade=MetricGrade.PASS
            if ratio >= 1.0
            else (MetricGrade.PARTIAL if ratio > 0 else MetricGrade.FAIL),
            rationale=f"{passes}/{total} rounds passed objective check",
        )
