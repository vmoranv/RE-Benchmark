"""Report export endpoints (JSON, CSV, batch)."""

from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import Response

from apps.api.container import get_repository

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

_CSV_COLUMNS = (
    "run_id",
    "dimension_code",
    "model_id",
    "state",
    "round_no",
    "round_state",
    "input_tokens",
    "output_tokens",
    "score",
    "created_at",
)


@router.get("/{run_id}/json")
async def export_json(run_id: UUID) -> dict:
    """Export full run data as JSON."""
    repo = get_repository()
    record = await repo.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return record.model_dump(mode="json")


@router.get("/{run_id}/csv")
async def export_csv(run_id: UUID) -> Response:
    """Export run metrics as CSV."""
    repo = get_repository()
    record = await repo.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_COLUMNS)
    writer.writeheader()

    base_row = {
        "run_id": str(record.id),
        "dimension_code": record.spec.dimension_code,
        "model_id": record.spec.model_id,
        "state": record.state.value,
        "created_at": record.created_at.isoformat(),
    }

    if record.rounds:
        for rnd in record.rounds:
            row = {**base_row}
            row["round_no"] = str(rnd.round_no)
            row["round_state"] = rnd.state
            row["input_tokens"] = str(rnd.input_tokens)
            row["output_tokens"] = str(rnd.output_tokens)
            row["score"] = rnd.metadata.get("score", "")
            writer.writerow(row)
    else:
        row = {
            **base_row,
            "round_no": "",
            "round_state": "",
            "input_tokens": "",
            "output_tokens": "",
            "score": "",
        }
        writer.writerow(row)

    filename = f"run_{record.id}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/batch/json")
async def export_batch_json(
    dimension_code: str | None = Query(default=None),
    model_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    """Export multiple runs as JSON, filtered by dimension and model."""
    repo = get_repository()
    items = await repo.list(limit=limit)

    if dimension_code is not None:
        items = [r for r in items if r.spec.dimension_code == dimension_code]
    if model_id is not None:
        items = [r for r in items if r.spec.model_id == model_id]

    return {
        "items": [r.model_dump(mode="json") for r in items],
        "total": len(items),
    }
