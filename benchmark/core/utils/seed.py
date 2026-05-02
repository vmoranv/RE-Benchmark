"""Deterministic seed derivation for reproducible runs (Q2)."""

from __future__ import annotations

import hashlib


def derive_seed(*parts: str | int | bytes, salt: bytes = b"js-re-bench-v1") -> int:
    """Derive a deterministic 63-bit positive integer seed from arbitrary parts.

    The output fits into a Postgres ``BIGINT`` and any 64-bit signed slot.
    """
    h = hashlib.blake2b(salt, digest_size=8)
    for part in parts:
        if isinstance(part, int):
            h.update(part.to_bytes(8, "big", signed=True))
        elif isinstance(part, bytes):
            h.update(part)
        else:
            h.update(str(part).encode("utf-8"))
        h.update(b"\x1f")  # unit separator
    digest = h.digest()
    value = int.from_bytes(digest, "big", signed=False)
    return value & ((1 << 63) - 1)
