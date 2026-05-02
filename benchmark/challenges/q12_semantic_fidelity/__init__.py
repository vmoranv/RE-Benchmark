"""Q12 Obfuscation Semantic Fidelity — gate on M8 ≥ 90% across sample suite."""

from __future__ import annotations

PASS_THRESHOLD = 0.9


def evaluate_fidelity(per_run_pass_ratios: list[float]) -> dict:
    if not per_run_pass_ratios:
        return {"ok": False, "reason": "no runs available", "score": 0.0}
    avg = sum(per_run_pass_ratios) / len(per_run_pass_ratios)
    return {
        "ok": avg >= PASS_THRESHOLD,
        "score": avg,
        "samples_evaluated": len(per_run_pass_ratios),
    }
