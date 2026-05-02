"""Token consumption metric (general #2)."""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricResult


class TokenConsumptionMetric(BaseMetric):
    code: ClassVar[str] = "token_consumption"
    name: ClassVar[str] = "Token Consumption (input + output)"
    unit: ClassVar[str] = "tokens"
    higher_is_better: ClassVar[bool] = False

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        total_in = sum(r.get("usage", {}).get("input_tokens", 0) for r in rounds)
        total_out = sum(r.get("usage", {}).get("output_tokens", 0) for r in rounds)
        total = total_in + total_out
        peak = max((r.get("usage", {}).get("output_tokens", 0) for r in rounds), default=0)
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=total,
            unit=self.unit,
            value_json={
                "input_tokens": total_in,
                "output_tokens": total_out,
                "peak_output_tokens": peak,
                "rounds_breakdown": [
                    {
                        "round_no": r.get("round_no"),
                        "input_tokens": r.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": r.get("usage", {}).get("output_tokens", 0),
                    }
                    for r in rounds
                ],
            },
            rationale=f"Total {total} tokens across {len(rounds)} rounds",
        )
