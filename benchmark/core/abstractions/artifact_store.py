"""ArtifactStore — content-addressed storage for arbitrary blobs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ArtifactStore(ABC):
    """Persists artifacts under their SHA-256 content hash.

    The store's invariant: the same ``content`` always maps to the same
    artifact id and storage uri (modulo concurrent first-writers). All
    references in the database are by artifact id; the bytes live in this
    store.
    """

    @abstractmethod
    async def put(
        self,
        content: bytes,
        *,
        mime_type: str,
        kind: str,
        metadata: dict | None = None,
    ) -> UUID:
        """Store ``content`` and return its artifact id."""

    @abstractmethod
    async def get(self, artifact_id: UUID) -> bytes:
        """Read the bytes for an artifact id. Raises if missing."""

    @abstractmethod
    async def head(self, artifact_id: UUID) -> dict:
        """Return artifact metadata without fetching bytes."""

    @abstractmethod
    async def exists(self, artifact_id: UUID) -> bool:
        """Cheap existence check."""
