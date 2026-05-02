"""Artifact-related domain models (content-addressed storage)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ArtifactKind(StrEnum):
    SOURCE = "source"
    TRACE = "trace"
    SCREENSHOT = "screenshot"
    HEAP = "heap"
    LOG = "log"
    REPORT = "report"
    PROMPT = "prompt"
    RESPONSE = "response"


class Artifact(BaseModel):
    """Content-addressed artifact metadata. Body lives in ArtifactStore."""

    id: UUID = Field(default_factory=uuid4)
    sha256: bytes = Field(min_length=32, max_length=32)
    size_bytes: int = Field(ge=0)
    mime_type: str
    storage_uri: str
    kind: ArtifactKind
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict = Field(default_factory=dict)

    @field_serializer("sha256", when_used="json")
    def _serialize_sha256(self, value: bytes) -> str:
        return value.hex()

    @field_validator("sha256", mode="before")
    @classmethod
    def _validate_sha256(cls, value: bytes | str) -> bytes:
        if isinstance(value, str):
            return bytes.fromhex(value)
        return value


class ArtifactRef(BaseModel):
    """Lightweight reference (only id + sha256), used in evidence chains."""

    id: UUID
    sha256: bytes

    @field_serializer("sha256", when_used="json")
    def _serialize_sha256(self, value: bytes) -> str:
        return value.hex()

    @field_validator("sha256", mode="before")
    @classmethod
    def _validate_sha256(cls, value: bytes | str) -> bytes:
        if isinstance(value, str):
            return bytes.fromhex(value)
        return value
