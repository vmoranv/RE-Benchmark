"""Filesystem-backed content-addressed artifact store."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from benchmark.core.abstractions.artifact_store import ArtifactStore
from benchmark.core.utils.content_hash import sha256_bytes, sha256_hex


class FilesystemArtifactStore(ArtifactStore):
    """Persists artifacts under ``<root>/<sha256[:2]>/<sha256[2:]>``.

    A separate ``metadata.json`` per shard records id, mime_type, kind,
    size, custom metadata. Suitable for development & single-node setups.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, sha_hex: str) -> Path:
        shard = sha_hex[:2]
        rest = sha_hex[2:]
        return self._root / shard / rest

    async def put(
        self,
        content: bytes,
        *,
        mime_type: str,
        kind: str,
        metadata: dict | None = None,
    ) -> UUID:
        sha_hex = sha256_hex(content)
        path = self._path_for(sha_hex)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        meta_path = path.with_suffix(".meta")
        if meta_path.exists():
            # Already stored, parse existing UUID
            import json

            existing = json.loads(meta_path.read_text(encoding="utf-8"))
            return UUID(existing["id"])
        artifact_id = uuid4()
        import json

        meta_path.write_text(
            json.dumps(
                {
                    "id": str(artifact_id),
                    "sha256": sha_hex,
                    "size_bytes": len(content),
                    "mime_type": mime_type,
                    "kind": kind,
                    "metadata": metadata or {},
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return artifact_id

    async def get(self, artifact_id: UUID) -> bytes:
        # Linear search by id is acceptable for the dev backend; production
        # adapters (S3) index by id directly.
        for meta_path in self._root.rglob("*.meta"):
            import json

            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if data["id"] == str(artifact_id):
                return meta_path.with_suffix("").read_bytes()
        msg = f"artifact {artifact_id} not found"
        raise FileNotFoundError(msg)

    async def head(self, artifact_id: UUID) -> dict:
        for meta_path in self._root.rglob("*.meta"):
            import json

            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if data["id"] == str(artifact_id):
                return data
        msg = f"artifact {artifact_id} not found"
        raise FileNotFoundError(msg)

    async def exists(self, artifact_id: UUID) -> bool:
        try:
            await self.head(artifact_id)
        except FileNotFoundError:
            return False
        return True

    async def put_with_known_hash(
        self, content: bytes, *, mime_type: str, kind: str
    ) -> tuple[UUID, bytes]:
        """Convenience that returns both id and sha256 digest."""
        artifact_id = await self.put(content, mime_type=mime_type, kind=kind)
        return artifact_id, sha256_bytes(content)
