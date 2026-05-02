"""Repository protocol — abstracts away DB vs in-memory persistence.

The default implementation (``InMemoryRunRepository``) is used during M2
to validate the orchestrator without forcing every test to spin up
PostgreSQL. The PG-backed repository ships in M2.4 once the schema
migration is wired into compose.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from benchmark.core.domain import RunRecord, RunRoundRecord, RunState


class RunRepository(ABC):
    """Persists and retrieves :class:`RunRecord` instances."""

    @abstractmethod
    async def insert(self, record: RunRecord) -> None: ...

    @abstractmethod
    async def get(self, run_id: UUID) -> RunRecord | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 50, offset: int = 0) -> list[RunRecord]: ...

    @abstractmethod
    async def update_state(
        self, run_id: UUID, state: RunState, *, error: str | None = None
    ) -> None: ...

    @abstractmethod
    async def append_round(self, run_id: UUID, round_record: RunRoundRecord) -> None: ...


class InMemoryRunRepository(RunRepository):
    """Process-local repository used in tests, dev, and the M1 API skeleton."""

    def __init__(self) -> None:
        self._runs: dict[UUID, RunRecord] = {}

    async def insert(self, record: RunRecord) -> None:
        self._runs[record.id] = record

    async def get(self, run_id: UUID) -> RunRecord | None:
        return self._runs.get(run_id)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[RunRecord]:
        items = sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)
        return items[offset : offset + limit]

    async def update_state(
        self, run_id: UUID, state: RunState, *, error: str | None = None
    ) -> None:
        record = self._runs.get(run_id)
        if not record:
            return
        record.state = state
        if error is not None:
            record.error = error

    async def append_round(self, run_id: UUID, round_record: RunRoundRecord) -> None:
        record = self._runs.get(run_id)
        if not record:
            return
        # Replace existing round with the same number for idempotent retries.
        record.rounds = [r for r in record.rounds if r.round_no != round_record.round_no]
        record.rounds.append(round_record)
        record.rounds.sort(key=lambda r: r.round_no)
