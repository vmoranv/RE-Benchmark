"""M2 — Hook Stealth Score.

Measures whether injected hooks trigger anti-hook detection scripts.
Lower detection rate = higher stealth.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M2HookStealthScore(BaseMetric):
    code: ClassVar[str] = "M2"
    name: ClassVar[str] = "Hook Stealth Score"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.5

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        detection_events = 0
        total_probes = 0
        for r in rounds:
            details = r.get("details", {})
            probes = details.get("hook_probes", [])
            if not probes:
                continue
            total_probes += len(probes)
            detection_events += sum(1 for p in probes if p.get("detected"))

        if total_probes == 0:
            return _fallback_score(run_record, rounds)

        stealth_ratio = 1.0 - (detection_events / total_probes)
        grade = (
            MetricGrade.PASS
            if stealth_ratio >= 0.8
            else MetricGrade.PARTIAL
            if stealth_ratio >= 0.4
            else MetricGrade.FAIL
        )
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=stealth_ratio,
            unit=self.unit,
            grade=grade,
            rationale=f"Hook detected in {detection_events}/{total_probes} probes (stealth={stealth_ratio:.1%}).",
        )


def _fallback_score(run_record: dict, rounds: list[dict]) -> MetricResult:
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    if ordered and ordered[0].get("score") is not None:
        return MetricResult(
            run_id=run_record["id"],
            metric_code="M2",
            value_num=float(ordered[0]["score"]),
            unit="percent",
            grade=MetricGrade.PARTIAL,
            rationale="No hook probe data; using round score as fallback.",
        )
    return MetricResult(
        run_id=run_record["id"],
        metric_code="M2",
        value_num=None,
        unit="percent",
        grade=MetricGrade.NOT_APPLICABLE,
        rationale="No hook stealth data available.",
    )
