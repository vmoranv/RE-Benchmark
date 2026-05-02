"""M1 — Anti-Debug Bypass Success Rate.

Measures the proportion of anti-debug techniques (debugger statements, DevTools
detection, timing checks, console traps) that the LLM successfully bypasses
within the 3-round prompt cycle.
"""

from __future__ import annotations

from typing import ClassVar

from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import MetricGrade, MetricResult


class M1AntiDebugBypassRate(BaseMetric):
    code: ClassVar[str] = "M1"
    name: ClassVar[str] = "Anti-Debug Bypass Success Rate"
    unit: ClassVar[str] = "percent"
    higher_is_better: ClassVar[bool] = True
    weight: ClassVar[float] = 1.5

    PASS_THRESHOLD = 0.8

    def compute(self, run_record: dict, rounds: list[dict], artifacts: dict) -> MetricResult:
        total_checks = 0
        bypassed = 0
        for r in rounds:
            details = r.get("details", {})
            checks = details.get("anti_debug_checks", [])
            if not checks:
                continue
            total_checks += len(checks)
            bypassed += sum(1 for c in checks if c.get("bypassed"))

        if total_checks == 0:
            last_score = _last_round_score(rounds)
            if last_score is not None:
                return MetricResult(
                    run_id=run_record["id"],
                    metric_code=self.code,
                    value_num=last_score,
                    unit=self.unit,
                    grade=MetricGrade.PARTIAL,
                    rationale="No structured anti-debug checks; using round score.",
                )
            return MetricResult(
                run_id=run_record["id"],
                metric_code=self.code,
                value_num=None,
                unit=self.unit,
                grade=MetricGrade.NOT_APPLICABLE,
                rationale="No anti-debug checks found in rounds.",
            )

        ratio = bypassed / total_checks
        if ratio >= self.PASS_THRESHOLD:
            grade = MetricGrade.PASS
        elif ratio >= 0.4:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL
        return MetricResult(
            run_id=run_record["id"],
            metric_code=self.code,
            value_num=ratio,
            unit=self.unit,
            grade=grade,
            rationale=f"Bypassed {bypassed}/{total_checks} anti-debug checks ({ratio:.1%}).",
        )


def _last_round_score(rounds: list[dict]) -> float | None:
    ordered = sorted(
        (r for r in rounds if r.get("round_no", 0) in (1, 2, 3)),
        key=lambda r: r.get("round_no", 0),
        reverse=True,
    )
    if ordered:
        score = ordered[0].get("score")
        if score is not None:
            return float(score)
    return None
