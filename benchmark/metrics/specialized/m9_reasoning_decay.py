"""M9 — LLM Reasoning Decay Rate.

Measures how quickly LLM task success rate drops as obfuscation level increases
from L1 to L5. A flatter decay curve means the model is more robust.

Computed as the negative slope of success_rate vs obfuscation_level.
Lower (absolute) slope = more robust = better.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M9ReasoningDecay(BaseMetric):
    code: ClassVar[str] = "M9"
    name: ClassVar[str] = "LLM Reasoning Decay Rate"
    unit: ClassVar[str] = "slope"
    higher_is_better: ClassVar[bool] = False
    weight: ClassVar[float] = 2.0

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        meta = run_record.get("metadata", {})
        decay_data = meta.get("decay_curve", [])

        if len(decay_data) < 2:
            return _fallback(run_record, rounds)

        # decay_data: [{"level": 1, "score": 0.95}, {"level": 2, "score": 0.88}, ...]
        levels = [d["level"] for d in decay_data if "level" in d and "score" in d]
        scores = [d["score"] for d in decay_data if "level" in d and "score" in d]

        if len(levels) < 2:
            return _fallback(run_record, rounds)

        slope = _linear_slope(levels, scores)
        abs_slope = abs(slope)

        # abs_slope: 0 = perfect (no decay), 0.2+ = steep decay
        grade = (
            MetricGrade.PASS
            if abs_slope <= 0.1
            else MetricGrade.PARTIAL
            if abs_slope <= 0.2
            else MetricGrade.FAIL
        )
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=slope,
            unit=self.unit,
            grade=grade,
            value_json={"levels": levels, "scores": scores},
            rationale=f"Decay slope = {slope:.4f} (flatter = more robust).",
        )


def _linear_slope(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys, strict=False))
    sum_x2 = sum(x * x for x in xs)
    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def _fallback(run_record: dict, rounds: list[dict]) -> MetricResult:
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    if ordered and ordered[0].get("score") is not None:
        return MetricResult(
            run_id=run_record["id"],
            metric_code="M9",
            value_num=float(ordered[0]["score"]),
            unit="slope",
            grade=MetricGrade.PARTIAL,
            rationale="Insufficient decay data; using round score.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M9",
        value_num=None,
        unit="slope",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="Insufficient decay curve data (need >= 2 levels).",
    )
