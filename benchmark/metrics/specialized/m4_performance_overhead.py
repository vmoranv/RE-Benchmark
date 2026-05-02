"""M4 — Real-Time Performance Overhead.

Measures the FPS drop, memory increase, and latency added by the RE tooling
on a target page. Lower overhead = better.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M4PerformanceOverhead(BaseMetric):
    code: ClassVar[str] = "M4"
    name: ClassVar[str] = "Real-Time Performance Overhead"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = False
    weight: ClassVar[float] = 1.0

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        perf = run_record.get("metadata", {}).get("performance", {})
        fps_drop = perf.get("fps_drop_percent")
        mem_increase = perf.get("memory_increase_percent")
        latency_increase = perf.get("latency_increase_percent")

        if fps_drop is None:
            return _fallback(run_record, rounds)

        avg_overhead = sum(filter(None, [fps_drop, mem_increase, latency_increase])) / sum(
            1 for v in [fps_drop, mem_increase, latency_increase] if v is not None
        )
        grade = (
            MetricGrade.PASS
            if avg_overhead <= 15
            else MetricGrade.PARTIAL
            if avg_overhead <= 30
            else MetricGrade.FAIL
        )
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=avg_overhead,
            unit=self.unit,
            grade=grade,
            rationale=(
                f"Avg overhead: {avg_overhead:.1f}% "
                f"(FPS={fps_drop}%, MEM={mem_increase}%, LAT={latency_increase}%)."
            ),
        )


def _fallback(run_record: dict, rounds: list[dict]) -> MetricResult:
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M4",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No performance overhead data collected.",
    )
