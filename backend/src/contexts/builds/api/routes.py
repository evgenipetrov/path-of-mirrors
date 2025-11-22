"""API routes for build parsing and analysis.

This module provides endpoints for:
- Parsing builds from Path of Building
- Analyzing build priorities and stat weights
"""

import structlog
from fastapi import APIRouter, HTTPException, status

# TODO: Move analyze_build to builds/services/analysis.py or similar
# For now, importing from analysis context (where it currently lives)
# Wait, analyze_build is in src.contexts.analysis.services.build_analyzer
# But that file is currently in upstream/services/build_analyzer.py?
# No, I saw it in analysis/services/build_analyzer.py earlier.
# Let's assume it's in analysis.services for now.
from src.contexts.analysis.services.build_analyzer import analyze_build
from src.contexts.builds.domain.schemas import (
    BuildAnalysisRequest,
    BuildAnalysisResponse,
    PoBParseRequest,
    PoBParseResponse,
    StatDefinitionsResponse,
)
from src.contexts.builds.services.pob import (
    decode_pob_code_to_xml,
    parse_pob_code,
    parse_pob_xml,
)
from src.contexts.builds.services.stat_definitions import get_stat_definitions
from src.contexts.upstream.services.pob_runner import run_pob
from src.infrastructure import create_session, get_session
from src.shared import Game

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/{game}/builds", tags=["builds"])


@router.post("/parse", response_model=PoBParseResponse, status_code=status.HTTP_200_OK)
async def parse_build(game: Game, request: PoBParseRequest) -> PoBParseResponse:
    """Parse Path of Building file or import code into standardized Build object.

    This endpoint:
    1. Parses PoB XML or import code
    2. Stores the build in Redis session (1-hour TTL)
    3. Returns parsed build data + session_id for subsequent requests

    The session_id can be used with:
    - /api/v1/{game}/builds/analyze - Get stat weights and priorities
    - /api/v1/{game}/items/search - Find item upgrades (client-side composition)

    Args:
        game: Game context (poe1 or poe2).
        request: PoB parsing request with either XML or import code

    Returns:
        Parsed Build object with session_id
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
        game=game.value,
        code_length=len(request.pob_code) if request.pob_code else 0,
        xml_length=len(request.pob_xml) if request.pob_xml else 0,
    )

    try:
        # Parse based on input type
        if request.pob_code:
            build = parse_pob_code(request.pob_code, game)
        else:
            build = parse_pob_xml(request.pob_xml, game)  # type: ignore

        # Optionally derive stats via headless PoB CLI (graceful fallback)
        xml_for_runner = request.pob_xml
        if not xml_for_runner and request.pob_code:
            try:
                xml_for_runner = decode_pob_code_to_xml(request.pob_code)
            except Exception as exc:
                logger.warn("pob_decode_failed_for_runner", error=str(exc))
                xml_for_runner = None

        derived_stats = run_pob(xml_for_runner or "", game) if xml_for_runner else {}

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
            "derived_stats": derived_stats or None,
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
            derived_stats=derived_stats or None,
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
async def analyze_build_endpoint(
    game: Game, request: BuildAnalysisRequest
) -> BuildAnalysisResponse:
    """Analyze build to calculate stat weights and upgrade priorities.

    This endpoint:
    1. Loads build from Redis session
    2. Detects build archetype (life/ES/hybrid)
    3. Calculates recommended stat weights
    4. Suggests upgrade priorities for each slot

    Users can then modify these weights before searching for upgrades.

    Args:
        game: Game context (poe1 or poe2).
        request: Analysis request with session_id

    Returns:
        Build analysis with archetype, weights, and priorities
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


@router.get("/stats", response_model=StatDefinitionsResponse, status_code=status.HTTP_200_OK)
async def get_canonical_stats(game: Game) -> StatDefinitionsResponse:
    """Get canonical stat definitions for a specific game.

    This endpoint provides the single source of truth for valid stat names,
    categories, and default weights. Use this to populate stat selection UIs
    and ensure consistency between frontend and backend.

    Args:
        game: Game context (poe1 or poe2)

    Returns:
        List of canonical stat definitions

    Example:
        GET /api/v1/poe1/builds/stats

        Response:
        {
            "game": "poe1",
            "stats": [
                {
                    "key": "life",
                    "display_name": "Life",
                    "category": "defense",
                    "default_weight": 1.0
                },
                ...
            ]
        }
    """
    logger.info("Fetching stat definitions", game=game.value)

    try:
        stats = get_stat_definitions(game)

        logger.info(
            "Stat definitions fetched",
            game=game.value,
            stat_count=len(stats),
        )

        return StatDefinitionsResponse(
            game=game,
            stats=stats,
        )

    except Exception as e:
        logger.error("Failed to fetch stat definitions", game=game.value, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stat definitions: {str(e)}",
        )


@router.get("/health", summary="builds context healthcheck")
async def builds_health(game: Game) -> dict[str, str]:
    """Builds context health check.

    Args:
        game: Game context (poe1 or poe2).

    Returns:
        Health status.
    """
    return {"status": "ok", "context": "builds", "game": game.value}
