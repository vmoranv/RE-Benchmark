"""Dimension catalog endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.container import get_dimension_registry

router = APIRouter(prefix="/api/v1/dimensions", tags=["dimensions"])


@router.get("/")
async def list_dimensions() -> dict:
    registry = get_dimension_registry()
    items = []
    for code, cls in sorted(registry.items()):
        items.append(
            {
                "code": code,
                "name": cls.name,
                "implemented": True,
                "paper_refs": cls.paper_refs,
            }
        )
    return {"items": items, "total": len(items)}
