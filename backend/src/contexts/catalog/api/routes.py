"""Placeholder routes for catalog context."""

from fastapi import APIRouter

from src.shared import Game

router = APIRouter(prefix="/api/v1/{game}/catalog", tags=["catalog"])


@router.get("/health", summary="catalog context healthcheck")
async def catalog_health(game: Game) -> dict[str, str]:
    """Catalog context health check.

    Args:
        game: Game context (poe1 or poe2).

    Returns:
        Health status.
    """
    return {"status": "ok", "context": "catalog", "game": game.value}
