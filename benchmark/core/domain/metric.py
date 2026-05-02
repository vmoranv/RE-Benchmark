"""Metric-related domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MetricGrade(StrEnum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    NOT_APPLICABLE = "n/a"


class MetricResult(BaseModel):
    """Result of computing a single metric for a run."""

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    metric_code: str
    value_num: float | None = None
    value_text: str | None = None
    value_json: dict | None = None
    unit: str | None = None
    grade: MetricGrade | None = None
    weight: float = 1.0
    rationale: str | None = None
    evidence_artifact_ids: list[UUID] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=_utcnow)
    metadata: dict = Field(default_factory=dict)
