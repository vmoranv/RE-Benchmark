"""Sample browser endpoints (skeleton)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/samples", tags=["samples"])


@router.get("/")
async def list_samples() -> dict:
    return {"items": [], "total": 0}
