"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-02 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "sample_family",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("dimension_code", sa.String(8), nullable=False, index=True),
        sa.Column("source", sa.String(16), nullable=False, index=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )

    op.create_table(
        "artifact",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sha256", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False, index=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )

    op.create_table(
        "sample_variant",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sample_family.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("obfuscation_level", sa.String(2), nullable=False, index=True),
        sa.Column("obfuscator", sa.Text()),
        sa.Column("obfuscator_version", sa.Text()),
        sa.Column("obfuscator_config", postgresql.JSONB()),
        sa.Column(
            "original_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact.id"),
            nullable=False,
        ),
        sa.Column(
            "obfuscated_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact.id"),
            nullable=False,
        ),
        sa.Column(
            "ground_truth_artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact.id")
        ),
        sa.Column("semantic_test_suite_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.CheckConstraint("obfuscation_level IN ('L1','L2','L3','L4','L5')", name="ck_sv_level"),
    )

    op.create_table(
        "run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("spec_digest", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column(
            "sample_variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sample_variant.id"),
            nullable=False,
        ),
        sa.Column("dimension_code", sa.String(8), nullable=False),
        sa.Column("model_id", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text()),
        sa.Column("state", sa.String(16), nullable=False, server_default="PLANNED"),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column("runner_image_digest", sa.Text()),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_run_dim_model", "run", ["dimension_code", "model_id"])
    op.create_index("idx_run_state", "run", ["state"])

    op.create_table(
        "run_round",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("run.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("round_no", sa.SmallInteger(), nullable=False),
        sa.Column(
            "prompt_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact.id"),
            nullable=False,
        ),
        sa.Column(
            "response_artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact.id")
        ),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_hit_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("state", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.UniqueConstraint("run_id", "round_no", name="uq_run_round"),
        sa.CheckConstraint("round_no IN (1,2,3,99)", name="ck_round_no"),
    )

    op.create_table(
        "metric_result",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("run.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("metric_code", sa.String(32), nullable=False, index=True),
        sa.Column("value_num", sa.Numeric()),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_json", postgresql.JSONB()),
        sa.Column("unit", sa.String(32)),
        sa.Column("grade", sa.String(16)),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.UniqueConstraint("run_id", "metric_code", name="uq_run_metric"),
    )

    op.create_table(
        "evidence_edge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("run.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("src_kind", sa.String(16), nullable=False),
        sa.Column("src_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dst_kind", sa.String(16), nullable=False),
        sa.Column("dst_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("rationale", sa.Text()),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )
    op.create_index("idx_evidence_src", "evidence_edge", ["src_kind", "src_id"])
    op.create_index("idx_evidence_dst", "evidence_edge", ["dst_kind", "dst_id"])

    op.create_table(
        "qualification_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge_code", sa.String(8), nullable=False, index=True),
        sa.Column("invoker", sa.String(16), nullable=False),
        sa.Column("git_sha", sa.String(40)),
        sa.Column("state", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("score", sa.Numeric(5, 2)),
        sa.Column("artifacts_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact.id")),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )

    op.create_table(
        "llm_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_digest", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("model_id", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text()),
        sa.Column(
            "request_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact.id"),
            nullable=False,
        ),
        sa.Column(
            "response_artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifact.id"),
            nullable=False,
        ),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6)),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), index=True),
    )

    op.create_table(
        "quota_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("period_key", sa.String(32), nullable=False),
        sa.Column("model_id", sa.Text()),
        sa.Column("tokens_consumed", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("budget_limit_usd", sa.Numeric(12, 2)),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("scope", "period", "period_key", "model_id", name="uq_quota_scope"),
    )
    op.create_index("idx_quota_scope_period", "quota_ledger", ["scope", "period_key"])


def downgrade() -> None:
    op.drop_table("quota_ledger")
    op.drop_table("llm_cache")
    op.drop_table("qualification_run")
    op.drop_table("evidence_edge")
    op.drop_table("metric_result")
    op.drop_table("run_round")
    op.drop_table("run")
    op.drop_table("sample_variant")
    op.drop_table("artifact")
    op.drop_table("sample_family")
