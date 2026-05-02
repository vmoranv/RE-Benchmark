"""Evidence-graph domain models."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceRelation(StrEnum):
    DERIVES_FROM = "derives_from"
    EVIDENCES = "evidences"
    CONTRADICTS = "contradicts"
    SUMMARIZES = "summarizes"


class EvidenceEdge(BaseModel):
    """A directed edge in the evidence DAG."""

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    src_kind: str
    src_id: UUID
    dst_kind: str
    dst_id: UUID
    relation: EvidenceRelation
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    rationale: str | None = None
    metadata: dict = Field(default_factory=dict)
