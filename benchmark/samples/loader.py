"""Load samples from on-disk seed directories into in-memory domain objects.

The convention used in M1/M2:

    benchmark/samples/seed_samples/<DIM_CODE>/<sample_name>/
        manifest.yaml       — metadata (id, level, obfuscator, semantic_test_cases, ...)
        original.js         — clean reference (private — not shipped to LLM)
        obfuscated.js       — input shown to the LLM
        ground_truth.js     — optional canonical solution (used by judges)
        tests/              — optional Jest/Vitest suite

A loader reads the manifest, ingests each file into the configured
``ArtifactStore``, and returns ``SampleFamily`` + ``SampleVariant`` Pydantic
models with stable UUIDs derived from the family name.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid5

import yaml

from benchmark.core.abstractions.artifact_store import ArtifactStore
from benchmark.core.domain import (
    ArtifactKind,
    ObfuscationLevel,
    SampleFamily,
    SampleSource,
    SampleVariant,
)

SEED_NAMESPACE = UUID("00000000-0000-0000-0000-000000000001")


def family_id(dimension_code: str, name: str) -> UUID:
    """Stable UUID5 for a sample family — ensures reproducible run-spec digests."""
    return uuid5(SEED_NAMESPACE, f"family::{dimension_code}::{name}")


def variant_id(family: UUID, level: str) -> UUID:
    return uuid5(SEED_NAMESPACE, f"variant::{family}::{level}")


class SampleLoadError(RuntimeError):
    """Raised when a sample directory is malformed."""


class SampleLoader:
    """Reads a sample directory tree and materializes domain objects.

    Stateless except for the bound :class:`ArtifactStore`. Safe to call
    repeatedly — the underlying CAS dedupes by SHA-256.
    """

    def __init__(self, artifact_store: ArtifactStore) -> None:
        self._store = artifact_store

    async def _parse_manifest(self, sample_dir: Path) -> dict:
        """Read and validate manifest.yaml."""
        manifest_path = sample_dir / "manifest.yaml"
        if not manifest_path.exists():
            msg = f"manifest.yaml missing in {sample_dir}"
            raise SampleLoadError(msg)
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        for required in ("id", "dimension_code", "obfuscation_level"):
            if required not in manifest:
                msg = f"manifest.yaml missing key: {required}"
                raise SampleLoadError(msg)
        return manifest

    async def _ingest_files(
        self, sample_dir: Path, sample_id: str
    ) -> tuple[UUID, UUID, UUID | None]:
        """Ingest original.js, obfuscated.js, and optional ground_truth.js."""
        original_path = sample_dir / "original.js"
        obfuscated_path = sample_dir / "obfuscated.js"
        if not original_path.exists() or not obfuscated_path.exists():
            msg = f"missing original.js or obfuscated.js in {sample_dir}"
            raise SampleLoadError(msg)

        orig_id = await self._store.put(
            original_path.read_bytes(),
            mime_type="application/javascript",
            kind=ArtifactKind.SOURCE.value,
            metadata={"role": "original", "sample": sample_id},
        )
        obf_id = await self._store.put(
            obfuscated_path.read_bytes(),
            mime_type="application/javascript",
            kind=ArtifactKind.SOURCE.value,
            metadata={"role": "obfuscated", "sample": sample_id},
        )
        gt_id: UUID | None = None
        gt_path = sample_dir / "ground_truth.js"
        if gt_path.exists():
            gt_id = await self._store.put(
                gt_path.read_bytes(),
                mime_type="application/javascript",
                kind=ArtifactKind.SOURCE.value,
                metadata={"role": "ground_truth", "sample": sample_id},
            )
        return orig_id, obf_id, gt_id

    async def load_directory(self, sample_dir: Path) -> tuple[SampleFamily, SampleVariant]:
        """Ingest the sample at ``sample_dir`` and return its domain pair."""
        manifest = await self._parse_manifest(sample_dir)
        original_id, obfuscated_id, gt_id = await self._ingest_files(sample_dir, manifest["id"])

        fam_id = family_id(manifest["dimension_code"], manifest["id"])
        family = SampleFamily(
            id=fam_id,
            name=manifest["id"],
            description=manifest.get("description"),
            dimension_code=manifest["dimension_code"],
            source=SampleSource(manifest.get("source", "synthetic")),
            metadata={"manifest_path": str(sample_dir / "manifest.yaml")},
        )

        variant = SampleVariant(
            id=variant_id(fam_id, manifest["obfuscation_level"]),
            family_id=fam_id,
            obfuscation_level=ObfuscationLevel(manifest["obfuscation_level"]),
            obfuscator=manifest.get("obfuscator"),
            obfuscator_version=manifest.get("obfuscator_version"),
            obfuscator_config=manifest.get("obfuscator_config") or {},
            original_artifact_id=original_id,
            obfuscated_artifact_id=obfuscated_id,
            ground_truth_artifact_id=gt_id,
            metadata={
                "obfuscated_size": (sample_dir / "obfuscated.js").stat().st_size,
                "semantic_test_cases": manifest.get("semantic_test_cases", []),
            },
        )
        return family, variant

    async def load_dimension(
        self, root: Path, dimension_code: str
    ) -> list[tuple[SampleFamily, SampleVariant]]:
        """Load every sample under ``root/<dimension_code>/``."""
        dim_dir = root / dimension_code
        if not dim_dir.exists():
            return []
        results: list[tuple[SampleFamily, SampleVariant]] = []
        for sample_dir in sorted(p for p in dim_dir.iterdir() if p.is_dir()):
            results.append(await self.load_directory(sample_dir))
        return results
