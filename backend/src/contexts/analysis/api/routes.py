"""API routes for analysis context."""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.contexts.analysis.services.ranking import (
    rank_upgrades,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


class RankRequest(BaseModel):
    """Request to rank candidate items against a target item.

    Attributes:
        target_item: The item being upgraded (PoB format)
        candidates: List of candidate items (PoB or Trade API format)
        stat_weights: Optional weights for scoring
    """

    target_item: dict
    candidates: list[dict]
    stat_weights: dict[str, float] | None = None


class RankResponse(BaseModel):
    """Response with ranked items.

    Attributes:
        ranked_items: List of items with scores, sorted by score
    """

    ranked_items: list[dict]


@router.post("/rank", response_model=RankResponse)
async def rank_items(request: RankRequest) -> RankResponse:
    """Rank candidate items against a target item.

    Args:
        request: Ranking request

    Returns:
        Ranked items with scores
    """
    logger.info(
        "Ranking items",
        num_candidates=len(request.candidates),
    )

    try:
        # Rank upgrades
        # Note: We don't have prices in the generic request yet, so passing None
        # In a real flow, prices should be extracted from candidates if available
        results = rank_upgrades(
            current_item=request.target_item,
            candidates=request.candidates,
            stat_weights=request.stat_weights,
        )

        # Convert UpgradeScore objects to dicts for response
        ranked_dicts = []
        for result in results:
            ranked_dicts.append(
                {
                    "score": result.score,
                    "improvements": result.improvements,
                    "stats": result.candidate_stats,
                    # We'd need to map back to the original item or include it
                    # For now, we'll just return the score and stats
                }
            )

        return RankResponse(ranked_items=ranked_dicts)

    except Exception as e:
        logger.error("Ranking failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rank items: {str(e)}",
        )


@router.get("/health", summary="analysis context healthcheck")
async def analysis_health() -> dict[str, str]:
    return {"status": "ok", "context": "analysis"}
