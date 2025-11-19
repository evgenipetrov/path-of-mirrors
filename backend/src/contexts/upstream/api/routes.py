"""API routes for upstream data sources.

This module provides universal endpoints for parsing and fetching data from
external sources like Path of Building, Trade API, and poe.ninja.
"""

import structlog
from fastapi import APIRouter, HTTPException, status

from src.contexts.upstream.domain.schemas import PoBParseRequest, PoBParseResponse
from src.contexts.upstream.services.pob_parser import parse_pob_code, parse_pob_xml

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/pob", tags=["pob"])


@router.post("/parse", response_model=PoBParseResponse, status_code=status.HTTP_200_OK)
async def parse_pob(request: PoBParseRequest) -> PoBParseResponse:
    """Parse Path of Building file or import code into standardized Build object.

    This is a universal endpoint that can be used by any feature:
    - Upgrade Finder: Parse build, extract current items, find better ones
    - Deal Finder: Parse build, identify item requirements, find deals
    - Meta Analyzer: Parse ladder builds, analyze trends

    Args:
        request: PoB parsing request with either XML or import code

    Returns:
        Standardized Build object with character info and items

    Raises:
        HTTPException 400: If neither pob_xml nor pob_code is provided
        HTTPException 422: If PoB data is invalid or cannot be parsed

    Example:
        POST /api/v1/pob/parse
        {
            "pob_code": "eNqVW2uT2zYS...",
            "game": "poe1"
        }

        Response:
        {
            "game": "poe1",
            "name": "RF Juggernaut",
            "character_class": "Marauder",
            "level": 95,
            "items": {...}
        }
    """
    # Validate that at least one input is provided
    if not request.pob_xml and not request.pob_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either pob_xml or pob_code must be provided",
        )

    # Log request details for debugging
    logger.info(
        "Parsing PoB request",
        has_xml=bool(request.pob_xml),
        has_code=bool(request.pob_code),
        game=request.game,
        code_length=len(request.pob_code) if request.pob_code else 0,
        xml_length=len(request.pob_xml) if request.pob_xml else 0,
    )

    try:
        # Parse based on input type
        if request.pob_code:
            build = parse_pob_code(request.pob_code, request.game)
        else:
            build = parse_pob_xml(request.pob_xml, request.game)  # type: ignore

        # Convert Build domain object to response schema
        response = PoBParseResponse(
            game=build.game,
            name=build.name,
            character_class=build.character_class,
            level=build.level,
            ascendancy=build.ascendancy,
            league=build.league,
            life=build.life,
            energy_shield=build.energy_shield,
            mana=build.mana,
            armour=build.armour,
            evasion=build.evasion,
            items=build.items,
            passive_tree=build.passive_tree,
            skills=build.skills,
            source=build.source or "pob",
        )

        logger.info(
            "Successfully parsed PoB",
            build_name=build.name,
            character_class=build.character_class,
            level=build.level,
            item_count=len(build.items) if build.items else 0,
        )

        return response

    except ValueError as e:
        # Invalid PoB data (malformed XML, missing fields, etc.)
        logger.warning("Invalid PoB data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid PoB data: {str(e)}",
        )
    except Exception as e:
        # Unexpected error
        logger.error("Unexpected error parsing PoB", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse PoB data: {str(e)}",
        )
