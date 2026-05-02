"""SQLAlchemy ORM models. Names mirror the DDL in `.claude/plan/js-re-bench.md` §2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class SampleFamilyORM(Base):
    __tablename__ = "sample_family"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    dimension_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    variants: Mapped[list[SampleVariantORM]] = relationship(back_populates="family")


class ArtifactORM(Base):
    __tablename__ = "artifact"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    sha256: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class SampleVariantORM(Base):
    __tablename__ = "sample_variant"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    family_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("sample_family.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    obfuscation_level: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    obfuscator: Mapped[str | None] = mapped_column(Text)
    obfuscator_version: Mapped[str | None] = mapped_column(Text)
    obfuscator_config: Mapped[dict | None] = mapped_column(JSONB)
    original_artifact_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id"), nullable=False
    )
    obfuscated_artifact_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id"), nullable=False
    )
    ground_truth_artifact_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id")
    )
    semantic_test_suite_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    family: Mapped[SampleFamilyORM] = relationship(back_populates="variants")
    __table_args__ = (
        CheckConstraint(
            "obfuscation_level IN ('L1','L2','L3','L4','L5')",
            name="ck_sv_level",
        ),
    )


class RunORM(Base):
    __tablename__ = "run"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    spec_digest: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    sample_variant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("sample_variant.id"), nullable=False
    )
    dimension_code: Mapped[str] = mapped_column(String(8), nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PLANNED")
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    runner_image_digest: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    rounds: Mapped[list[RunRoundORM]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    metric_results: Mapped[list[MetricResultORM]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_run_dim_model", "dimension_code", "model_id"),
        Index("idx_run_state", "state"),
    )


class RunRoundORM(Base):
    __tablename__ = "run_round"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    prompt_artifact_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id"), nullable=False
    )
    response_artifact_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id")
    )
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_hit_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    run: Mapped[RunORM] = relationship(back_populates="rounds")
    __table_args__ = (
        UniqueConstraint("run_id", "round_no", name="uq_run_round"),
        CheckConstraint("round_no IN (1,2,3,99)", name="ck_round_no"),
    )


class MetricResultORM(Base):
    __tablename__ = "metric_result"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    value_num: Mapped[float | None] = mapped_column(Numeric)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    unit: Mapped[str | None] = mapped_column(String(32))
    grade: Mapped[str | None] = mapped_column(String(16))
    weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    run: Mapped[RunORM] = relationship(back_populates="metric_results")
    __table_args__ = (UniqueConstraint("run_id", "metric_code", name="uq_run_metric"),)


class EvidenceEdgeORM(Base):
    __tablename__ = "evidence_edge"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("run.id", ondelete="CASCADE"), nullable=False, index=True
    )
    src_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    src_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    dst_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    dst_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    relation: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    rationale: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_evidence_src", "src_kind", "src_id"),
        Index("idx_evidence_dst", "dst_kind", "dst_id"),
    )


class QualificationRunORM(Base):
    __tablename__ = "qualification_run"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    challenge_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    invoker: Mapped[str] = mapped_column(String(16), nullable=False)
    git_sha: Mapped[str | None] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="RUNNING")
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    artifacts_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id")
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class LLMCacheORM(Base):
    __tablename__ = "llm_cache"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    request_digest: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    request_artifact_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id"), nullable=False
    )
    response_artifact_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("artifact.id"), nullable=False
    )
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class QuotaLedgerORM(Base):
    __tablename__ = "quota_ledger"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    period_key: Mapped[str] = mapped_column(String(32), nullable=False)
    model_id: Mapped[str | None] = mapped_column(Text)
    tokens_consumed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    budget_limit_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("scope", "period", "period_key", "model_id", name="uq_quota_scope"),
        Index("idx_quota_scope_period", "scope", "period_key"),
    )
