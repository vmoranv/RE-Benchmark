"""Run submission and inspection endpoints.

Supports all 18 dimensions via the dimension registry and multi-model
selection (anthropic/*, openai/*, mock/*).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from apps.api.container import (
    build_dimension,
    get_artifact_store,
    get_model,
    get_repository,
    get_run_service,
)
from benchmark.core.domain import RunSpec
from benchmark.samples.loader import SampleLoader

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("/", status_code=201)
async def submit_run(
    spec: RunSpec,
    execute: bool = Query(default=False, description="Run synchronously after submit"),
) -> dict:
    """Create a run. With ``execute=true`` runs the full pipeline before returning."""
    service = get_run_service()
    record = await service.submit(spec)
    if not execute:
        return record.model_dump(mode="json")

    dimension = build_dimension(spec.dimension_code)
    if dimension is None:
        raise HTTPException(
            status_code=400,
            detail=f"dimension {spec.dimension_code} is not implemented",
        )
    sample = await _resolve_sample(spec)
    if sample is None:
        raise HTTPException(status_code=404, detail="sample not found")
    final = await service.execute(
        record.id,
        dimension=dimension,
        sample=sample,
        model=get_model(spec.model_id),
    )
    return final.model_dump(mode="json")


@router.get("/")
async def list_runs(limit: int = 50, offset: int = 0) -> dict:
    repo = get_repository()
    items = await repo.list(limit=limit, offset=offset)
    return {
        "items": [r.model_dump(mode="json") for r in items],
        "total": len(items),
    }


@router.get("/{run_id}")
async def get_run(run_id: UUID) -> dict:
    repo = get_repository()
    record = await repo.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return record.model_dump(mode="json")


# ---------------------------------------------------------------------------


async def _resolve_sample(spec: RunSpec):
    """Resolve a sample from the seed_samples directory."""
    seed_root = Path("benchmark/samples/seed_samples").resolve()
    if not seed_root.exists():
        return None
    loader = SampleLoader(get_artifact_store())
    pairs = await loader.load_dimension(seed_root, spec.dimension_code)
    for _family, variant in pairs:
        if variant.id == spec.sample_variant_id:
            return variant
    return None
