"""Determinism verification tests (Q2 — same input ⇒ same output)."""

from __future__ import annotations

from benchmark.challenges.q02_deterministic import diff_runs


def test_diff_identifies_identical_runs():
    a = {"id": "1", "started_at": "ts1", "metric": [1, 2, 3]}
    b = {"id": "2", "started_at": "ts2", "metric": [1, 2, 3]}
    res = diff_runs(a, b)
    assert res["identical"] is True


def test_diff_detects_payload_differences():
    a = {"metric": [1, 2, 3]}
    b = {"metric": [1, 2, 4]}
    res = diff_runs(a, b)
    assert res["identical"] is False
