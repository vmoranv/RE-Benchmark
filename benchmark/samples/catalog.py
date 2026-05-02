"""Tiny seed sample for D1 deobfuscation: original + obfuscated pair."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid5

# Deterministic UUID namespace for seed samples (so M1 tests are reproducible)
SEED_NAMESPACE = UUID("00000000-0000-0000-0000-000000000001")


def seed_sample_id(name: str) -> UUID:
    return uuid5(SEED_NAMESPACE, name)


SEED_DIR = Path(__file__).parent / "seed_samples" / "D01"
