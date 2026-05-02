"""Tests for deterministic seed derivation."""

from __future__ import annotations

from benchmark.core.utils.seed import derive_seed


def test_derive_seed_deterministic():
    a = derive_seed("run", 1, "x")
    b = derive_seed("run", 1, "x")
    assert a == b
    assert 0 <= a < (1 << 63)


def test_derive_seed_changes_with_inputs():
    assert derive_seed("a") != derive_seed("b")
    assert derive_seed(1) != derive_seed(2)
    assert derive_seed("x", 1) != derive_seed("x", 2)


def test_derive_seed_salt_isolates():
    assert derive_seed("x", salt=b"alpha") != derive_seed("x", salt=b"beta")
