"""Canonical JSON encoder for Q2 deterministic-metric reproducibility.

Rules (a strict subset of RFC 8785 sufficient for our needs):

* keys sorted lexicographically (UTF-8 byte order)
* no insignificant whitespace
* UTF-8 output, no escape of non-ASCII unless required
* floats rendered via :func:`json.dumps` with ``allow_nan=False``
* ``None``, ``bool``, ``int`` rendered as default
* dicts and lists recursed
* tuples are treated as lists

Anything outside this whitelist (sets, datetimes, bytes, custom objects)
must be pre-converted by the caller.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize(obj: Any) -> str:
    """Serialize ``obj`` into a canonical JSON text."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonicalize_bytes(obj: Any) -> bytes:
    """Canonical JSON as UTF-8 bytes (suitable for hashing)."""
    return canonicalize(obj).encode("utf-8")
