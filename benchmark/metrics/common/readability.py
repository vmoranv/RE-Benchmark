"""Readability metric (general #4) — placeholder using LLM-as-judge."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricResult


class ReadabilityMetric(BaseMetric):
    code: ClassVar[str] = "readability"
    name: ClassVar[str] = "Readability (LLM-as-judge composite)"
    unit: ClassVar[str] = "score_0_10"
    higher_is_better: ClassVar[bool] = True

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        # The judge round (round_no=99) is expected to populate
        # parsed.readability_score in [0, 10]. Fall back to 0.
        judge = next((r for r in rounds if r.get("round_no") == 99), None)
        score = (judge or {}).get("parsed", {}).get("readability_score", 0.0)
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=float(score),
            unit=self.unit,
            rationale="Readability sourced from JUDGE round; defaults to 0 if no judge present.",
        )
