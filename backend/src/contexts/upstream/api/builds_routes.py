"""API routes for build parsing and analysis.

This module provides endpoints for:
- Parsing builds from Path of Building
- Analyzing build priorities and stat weights
- Searching for upgrades
"""

import structlog
from fastapi import APIRouter, HTTPException, status

from src.contexts.analysis.services import analyze_build
from src.contexts.upstream.domain.schemas import (
    BuildAnalysisRequest,
    BuildAnalysisResponse,
    PoBParseRequest,
    PoBParseResponse,
)
from src.contexts.upstream.services.pob_parser import parse_pob_code, parse_pob_xml
from src.infrastructure import create_session, get_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/builds", tags=["builds"])


@router.post("/parse", response_model=PoBParseResponse, status_code=status.HTTP_200_OK)
async def parse_build(request: PoBParseRequest) -> PoBParseResponse:
    """Parse Path of Building file or import code into standardized Build object.

    This endpoint:
    1. Parses PoB XML or import code
    2. Stores the build in Redis session (1-hour TTL)
    3. Returns parsed build data + session_id for subsequent requests

    The session_id can be used with:
    - /api/v1/builds/analyze - Get stat weights and priorities
    - /api/v1/builds/upgrades/search - Find item upgrades

    Args:
        request: PoB parsing request with either XML or import code

    Returns:
        Parsed Build object with session_id

    Raises:
        HTTPException 400: If neither pob_xml nor pob_code is provided
        HTTPException 422: If PoB data is invalid or cannot be parsed

    Example:
        POST /api/v1/builds/parse
        {
            "pob_code": "eNqVW2uT2zYS...",
            "game": "poe1"
        }

        Response:
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
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
        "Parsing build request",
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

        # Store build in Redis session
        session_data = {
            "build": {
                "game": build.game.value,
                "name": build.name,
                "character_class": build.character_class,
                "level": build.level,
                "ascendancy": build.ascendancy,
                "league": build.league,
                "life": build.life,
                "energy_shield": build.energy_shield,
                "mana": build.mana,
                "armour": build.armour,
                "evasion": build.evasion,
                "items": build.items,
                "passive_tree": build.passive_tree,
                "skills": build.skills,
                "source": build.source or "pob",
            },
            "pob_code": request.pob_code,  # Store for future re-parsing if needed
        }

        session_id = await create_session(session_data)

        # Convert Build domain object to response schema
        response = PoBParseResponse(
            session_id=session_id,
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
            "Successfully parsed build",
            session_id=session_id,
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


@router.post("/analyze", response_model=BuildAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_build_endpoint(request: BuildAnalysisRequest) -> BuildAnalysisResponse:
    """Analyze build to calculate stat weights and upgrade priorities.

    This endpoint:
    1. Loads build from Redis session
    2. Detects build archetype (life/ES/hybrid)
    3. Calculates recommended stat weights
    4. Suggests upgrade priorities for each slot

    Users can then modify these weights before searching for upgrades.

    Args:
        request: Analysis request with session_id

    Returns:
        Build analysis with archetype, weights, and priorities

    Raises:
        HTTPException 404: If session not found or expired
        HTTPException 500: For unexpected errors

    Example:
        POST /api/v1/builds/analyze
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000"
        }

        Response:
        {
            "archetype": "life_based",
            "suggested_weights": {
                "life": 2.0,
                "fire_res": 0.8,
                ...
            },
            "upgrade_priorities": {
                "Amulet": ["life", "fire_res", "cold_res"],
                ...
            },
            "current_stats": {
                "life": 5000,
                "energy_shield": null,
                "level": 85
            }
        }
    """
    logger.info("Analyzing build", session_id=request.session_id)

    # Load build from session
    session_data = await get_session(request.session_id)

    if session_data is None:
        logger.warning("Session not found", session_id=request.session_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found or expired",
        )

    try:
        # Extract build data
        build_data = session_data.get("build", {})

        # Perform analysis
        analysis = analyze_build(build_data)

        logger.info(
            "Build analysis complete",
            session_id=request.session_id,
            archetype=analysis["archetype"],
        )

        return BuildAnalysisResponse(
            archetype=analysis["archetype"],
            suggested_weights=analysis["suggested_weights"],
            upgrade_priorities=analysis["upgrade_priorities"],
            current_stats=analysis["current_stats"],
        )

    except Exception as e:
        logger.error(
            "Error analyzing build",
            session_id=request.session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze build: {str(e)}",
        )
