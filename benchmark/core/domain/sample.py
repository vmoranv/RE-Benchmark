"""Sample-related domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ObfuscationLevel(StrEnum):
    L1 = "L1"  # Lexical
    L2 = "L2"  # Structural (CFF, dead code)
    L3 = "L3"  # Data (string array, encoding)
    L4 = "L4"  # Semantic (proxies, eval)
    L5 = "L5"  # Virtualization (JSVMP)


class SampleSource(StrEnum):
    SYNTHETIC = "synthetic"
    WILD = "wild"
    BLIND = "blind"


class SampleFamily(BaseModel):
    """A family groups variants of the same original problem under different obfuscations."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    dimension_code: str
    source: SampleSource
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict = Field(default_factory=dict)


class SampleVariant(BaseModel):
    """A specific obfuscated variant of a sample."""

    id: UUID = Field(default_factory=uuid4)
    family_id: UUID
    obfuscation_level: ObfuscationLevel
    obfuscator: str | None = None
    obfuscator_version: str | None = None
    obfuscator_config: dict = Field(default_factory=dict)
    original_artifact_id: UUID
    obfuscated_artifact_id: UUID
    ground_truth_artifact_id: UUID | None = None
    semantic_test_suite_id: UUID | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict = Field(default_factory=dict)
