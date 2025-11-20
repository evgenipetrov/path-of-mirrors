"""API routes for economy context."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.contexts.economy.services.trade import build_simple_query, search_and_fetch_items
from src.shared import Game

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/item", tags=["economy"])


class ItemSearchRequest(BaseModel):
    """Request to search for items on Trade API.

    Attributes:
        game: Game context (POE1 or POE2)
        league: League name
        item_type: Base type name (e.g., "Jade Amulet")
        min_life: Minimum life requirement
        max_price_chaos: Maximum price in chaos orbs
        limit: Maximum number of results to return
    """

    game: Game
    league: str
    item_type: str = Field(..., min_length=1)
    min_life: int | None = Field(None, ge=0)
    max_price_chaos: float | None = Field(None, ge=0)
    limit: int = Field(10, ge=1, le=50)


class ItemSearchResponse(BaseModel):
    """Response with item search results.

    Attributes:
        items: List of raw item data from Trade API
        total: Total number of results found
    """

    items: list[dict]
    total: int


@router.post("/search", response_model=ItemSearchResponse)
async def search_items(request: ItemSearchRequest) -> ItemSearchResponse:
    """Search for items on Trade API.

    This is a direct proxy to the Trade API with simplified filtering.
    It does NOT perform any ranking or analysis.

    Args:
        request: Search request parameters

    Returns:
        List of items found
    """
    logger.info(
        "Item search request",
        game=request.game.value,
        league=request.league,
        item_type=request.item_type,
    )

    # Build query
    query = build_simple_query(
        item_type=request.item_type,
        min_life=request.min_life,
        max_price_chaos=int(request.max_price_chaos) if request.max_price_chaos else None,
    )

    # Execute search
    try:
        items = await search_and_fetch_items(
            game=request.game,
            league=request.league,
            query=query,
            limit=request.limit,
        )
    except Exception as e:
        logger.error("Item search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search items: {str(e)}",
        )

    return ItemSearchResponse(
        items=items,
        total=len(items),
    )
