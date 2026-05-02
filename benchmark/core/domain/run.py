"""Run-related domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


def _utcnow() -> datetime:
    """Timezone-aware UTC ``now`` (replacement for the deprecated ``datetime.utcnow()``)."""
    return datetime.now(UTC)


class RunState(StrEnum):
    PLANNED = "PLANNED"
    PRECHECK = "PRECHECK"
    R1 = "R1"
    V1 = "V1"
    R2 = "R2"
    V2 = "V2"
    R3 = "R3"
    V3 = "V3"
    JUDGE = "JUDGE"
    METRICS = "METRICS"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"


class RunSpec(BaseModel):
    """Input specification for a run. Hash of canonical-JSON form is `spec_digest`."""

    sample_variant_id: UUID
    dimension_code: str = Field(min_length=2, max_length=8)
    model_id: str = Field(min_length=1)
    model_version: str | None = None
    seed: int = Field(ge=0, le=2**63 - 1)
    rounds: int = Field(default=3, ge=1, le=3)
    challenge_overrides: dict = Field(default_factory=dict)
    metric_codes: list[str] = Field(default_factory=list)
    judge_model_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class RunRoundRecord(BaseModel):
    """Record of a single round execution (R1, R2, R3, or JUDGE)."""

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    round_no: int = Field(ge=1, le=99)
    prompt_artifact_id: UUID
    response_artifact_id: UUID | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    cost_usd: float | None = None
    latency_ms: int | None = None
    state: str = "PENDING"
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class RunRecord(BaseModel):
    """Full record of a benchmark run."""

    id: UUID = Field(default_factory=uuid4)
    spec_digest: bytes
    spec: RunSpec
    state: RunState = RunState.PLANNED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    runner_image_digest: str | None = None
    rounds: list[RunRoundRecord] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict = Field(default_factory=dict)

    @field_serializer("spec_digest", when_used="json")
    def _serialize_spec_digest(self, value: bytes) -> str:
        return value.hex()

    @field_validator("spec_digest", mode="before")
    @classmethod
    def _validate_spec_digest(cls, value: bytes | str) -> bytes:
        if isinstance(value, str):
            return bytes.fromhex(value)
        return value
