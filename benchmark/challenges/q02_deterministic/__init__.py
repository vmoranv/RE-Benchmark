"""Q2 Deterministic Metrics — replay a run twice and diff canonical output."""

from __future__ import annotations

from benchmark.core.utils.canonical_json import canonicalize


def diff_runs(
    run_a: dict,
    run_b: dict,
    *,
    ignore_keys: tuple[str, ...] = ("started_at", "finished_at", "computed_at", "id"),
) -> dict:
    """Return a structured diff between two run records.

    Volatile fields (timestamps, IDs) are stripped before comparison so
    deterministic logic can be checked even when wall-clock timing differs.
    """

    def _strip(obj):
        if isinstance(obj, dict):
            return {k: _strip(v) for k, v in obj.items() if k not in ignore_keys}
        if isinstance(obj, list):
            return [_strip(v) for v in obj]
        return obj

    a = canonicalize(_strip(run_a))
    b = canonicalize(_strip(run_b))
    return {"identical": a == b, "left": a, "right": b}
