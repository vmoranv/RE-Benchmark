"""SHA-256 helpers for content-addressed storage."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def sha256_bytes(data: bytes) -> bytes:
    """Compute SHA-256 of ``data``, returning the 32-byte digest."""
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    """Hexadecimal SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_chunks(chunks: Iterable[bytes]) -> bytes:
    """SHA-256 of streamed chunks (avoids materializing large blobs)."""
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.digest()
