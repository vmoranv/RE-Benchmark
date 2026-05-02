"""PostgreSQL-backed :class:`RunRepository` using async SQLAlchemy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from benchmark.core.domain import RunRecord, RunRoundRecord, RunState
from benchmark.core.persistence.models import RunORM, RunRoundORM
from benchmark.core.persistence.repositories.runs import RunRepository
from benchmark.core.persistence.session import session_scope


class PostgresRunRepository(RunRepository):
    """Persist runs in PostgreSQL via async SQLAlchemy."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # Helpers: domain <-> ORM conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _round_to_orm(rec: RunRoundRecord) -> RunRoundORM:
        return RunRoundORM(
            id=rec.id,
            run_id=rec.run_id,
            round_no=rec.round_no,
            prompt_artifact_id=rec.prompt_artifact_id,
            response_artifact_id=rec.response_artifact_id,
            input_tokens=rec.input_tokens,
            output_tokens=rec.output_tokens,
            cache_hit_tokens=rec.cache_hit_tokens,
            cost_usd=rec.cost_usd,
            latency_ms=rec.latency_ms,
            state=rec.state,
            error=rec.error,
            started_at=rec.started_at,
            finished_at=rec.finished_at,
            extra=rec.metadata,
        )

    @staticmethod
    def _orm_round_to_domain(orm: RunRoundORM) -> RunRoundRecord:
        return RunRoundRecord(
            id=orm.id,
            run_id=orm.run_id,
            round_no=orm.round_no,
            prompt_artifact_id=orm.prompt_artifact_id,
            response_artifact_id=orm.response_artifact_id,
            input_tokens=orm.input_tokens,
            output_tokens=orm.output_tokens,
            cache_hit_tokens=orm.cache_hit_tokens,
            cost_usd=float(orm.cost_usd) if orm.cost_usd is not None else None,
            latency_ms=orm.latency_ms,
            state=orm.state,
            error=orm.error,
            started_at=orm.started_at,
            finished_at=orm.finished_at,
            metadata=orm.extra,
        )

    @staticmethod
    def _orm_to_domain(orm: RunORM) -> RunRecord:
        return RunRecord(
            id=orm.id,
            spec_digest=orm.spec_digest,
            spec=orm.config,  # JSONB -> RunSpec via Pydantic model_validate
            state=orm.state,
            started_at=orm.started_at,
            finished_at=orm.finished_at,
            error=orm.error,
            runner_image_digest=orm.runner_image_digest,
            rounds=[PostgresRunRepository._orm_round_to_domain(r) for r in orm.rounds],
            created_at=orm.created_at,
            metadata=orm.extra,
        )

    # ------------------------------------------------------------------
    # Repository interface
    # ------------------------------------------------------------------

    async def insert(self, record: RunRecord) -> None:
        orm = RunORM(
            id=record.id,
            spec_digest=record.spec_digest,
            sample_variant_id=record.spec.sample_variant_id,
            dimension_code=record.spec.dimension_code,
            model_id=record.spec.model_id,
            model_version=record.spec.model_version,
            state=record.state,
            seed=record.spec.seed,
            started_at=record.started_at,
            finished_at=record.finished_at,
            error=record.error,
            runner_image_digest=record.runner_image_digest,
            config=record.spec.model_dump(mode="json"),
            extra=record.metadata,
            rounds=[self._round_to_orm(r) for r in record.rounds],
        )
        async with session_scope(self._session_factory) as session:
            session.add(orm)

    async def get(self, run_id: UUID) -> RunRecord | None:
        stmt = select(RunORM).where(RunORM.id == run_id).options(selectinload(RunORM.rounds))
        async with session_scope(self._session_factory) as session:
            result = await session.execute(stmt)
            orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return self._orm_to_domain(orm)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[RunRecord]:
        stmt = (
            select(RunORM)
            .order_by(RunORM.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(RunORM.rounds))
        )
        async with session_scope(self._session_factory) as session:
            result = await session.execute(stmt)
            orms = result.scalars().all()
        return [self._orm_to_domain(o) for o in orms]

    async def update_state(
        self, run_id: UUID, state: RunState, *, error: str | None = None
    ) -> None:
        values: dict = {"state": state}
        if error is not None:
            values["error"] = error
        stmt = update(RunORM).where(RunORM.id == run_id).values(**values)
        async with session_scope(self._session_factory) as session:
            await session.execute(stmt)

    async def append_round(self, run_id: UUID, round_record: RunRoundRecord) -> None:
        async with session_scope(self._session_factory) as session:
            # Check if a round with this run_id + round_no already exists.
            existing = await session.execute(
                select(RunRoundORM).where(
                    RunRoundORM.run_id == run_id,
                    RunRoundORM.round_no == round_record.round_no,
                )
            )
            existing_orm = existing.scalar_one_or_none()
            if existing_orm is not None:
                # Upsert: update existing round fields.
                existing_orm.prompt_artifact_id = round_record.prompt_artifact_id
                existing_orm.response_artifact_id = round_record.response_artifact_id
                existing_orm.input_tokens = round_record.input_tokens
                existing_orm.output_tokens = round_record.output_tokens
                existing_orm.cache_hit_tokens = round_record.cache_hit_tokens
                existing_orm.cost_usd = round_record.cost_usd
                existing_orm.latency_ms = round_record.latency_ms
                existing_orm.state = round_record.state
                existing_orm.error = round_record.error
                existing_orm.started_at = round_record.started_at
                existing_orm.finished_at = round_record.finished_at
                existing_orm.extra = round_record.metadata
            else:
                # Insert new round.
                orm = self._round_to_orm(round_record)
                orm.run_id = run_id
                session.add(orm)
