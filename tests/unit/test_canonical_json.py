"""Tests for canonical JSON encoding (Q2 determinism)."""

from __future__ import annotations

from benchmark.core.utils.canonical_json import canonicalize, canonicalize_bytes


def test_canonicalize_sorts_keys():
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert canonicalize(a) == canonicalize(b) == '{"a":2,"b":1}'


def test_canonicalize_no_whitespace():
    assert canonicalize({"x": [1, 2, 3]}) == '{"x":[1,2,3]}'


def test_canonicalize_unicode_preserved():
    out = canonicalize({"name": "你好"})
    assert "你好" in out


def test_canonicalize_bytes_is_utf8():
    raw = canonicalize_bytes({"k": "v"})
    assert isinstance(raw, bytes)
    assert raw == b'{"k":"v"}'


def test_canonicalize_rejects_nan():
    import math

    import pytest

    with pytest.raises(ValueError):
        canonicalize({"x": math.nan})
