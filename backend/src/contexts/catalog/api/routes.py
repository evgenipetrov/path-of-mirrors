"""Placeholder routes for catalog context."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/health", summary="catalog context healthcheck")
async def catalog_health() -> dict[str, str]:
    return {"status": "ok", "context": "catalog"}
