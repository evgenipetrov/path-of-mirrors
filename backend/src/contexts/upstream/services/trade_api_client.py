"""Trade API client for Path of Exile trade searches.

This module provides functions to search for items on pathofexile.com/trade API.

Trade API Flow:
1. POST to /api/trade/search/{league} with query → Get result IDs
2. GET /api/trade/fetch/{result_ids} → Get item details

Rate Limits (per docs):
- Search: 1 request per second per IP
- Fetch: 1 request per second per IP
- Bursts allowed: 5 requests

API Documentation:
https://www.pathofexile.com/developer/docs/reference#trade
"""

from typing import Any

import structlog

from src.shared import Game
from src.shared.http import create_poe_http_client

logger = structlog.get_logger(__name__)


# Trade API base URLs
TRADE_API_URLS = {
    Game.POE1: "https://www.pathofexile.com/api/trade",
    Game.POE2: "https://www.pathofexile.com/api/trade2",  # TODO: Verify PoE2 URL when available
}


async def search_items(
    game: Game,
    league: str,
    query: dict[str, Any],
    limit: int = 10,
) -> list[str]:
    """Search for items on Trade API.

    Phase 1 (MVP): Basic search with minimal query structure.
    Returns item IDs that can be fetched for details.

    Args:
        game: Game context (POE1 or POE2)
        league: League name (e.g., "Affliction", "Standard")
        query: Trade API query structure
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of item result IDs

    Raises:
        httpx.HTTPStatusError: For API errors (rate limit, invalid query, etc.)

    Example:
        >>> query = {
        ...     "query": {
        ...         "type": "Jade Amulet",
        ...         "stats": [{"type": "and", "filters": [...]}]
        ...     }
        ... }
        >>> item_ids = await search_items(Game.POE1, "Standard", query)
        >>> print(item_ids)  # ['abc123', 'def456', ...]
    """
    base_url = TRADE_API_URLS[game]
    search_url = f"{base_url}/search/{league}"

    logger.info(
        "Searching Trade API",
        game=game.value,
        league=league,
        query_type=query.get("query", {}).get("type"),
        limit=limit,
    )

    try:
        client = get_http_client()
        response = await client.post(search_url, json=query)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        # Extract result IDs (limit to requested amount)
        result_ids: list[str] = data.get("result", [])[:limit]

        logger.info(
            "Trade search complete",
            total_results=data.get("total", 0),
            returned_ids=len(result_ids),
        )

        return result_ids

    except Exception as e:
        logger.error(
            "Trade search failed",
            game=game.value,
            league=league,
            error=str(e),
        )
        raise


async def fetch_items(
    game: Game,
    result_ids: list[str],
    query_id: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch item details from Trade API.

    Args:
        game: Game context (POE1 or POE2)
        result_ids: List of item IDs from search_items()
        query_id: Optional query ID from search (used for tracking)

    Returns:
        List of item detail dictionaries

    Raises:
        httpx.HTTPStatusError: For API errors

    Example:
        >>> items = await fetch_items(Game.POE1, ['abc123', 'def456'])
        >>> print(items[0]['item']['name'])  # "Corruption Choker"
    """
    if not result_ids:
        logger.warning("No result IDs to fetch")
        return []

    base_url = TRADE_API_URLS[game]

    # Trade API accepts up to 10 items per fetch request
    # Format: /api/trade/fetch/{id1,id2,id3}
    ids_param = ",".join(result_ids[:10])  # Limit to 10 for MVP
    fetch_url = f"{base_url}/fetch/{ids_param}"

    # Add query_id as query param if provided (helps with rate limiting)
    params = {"query": query_id} if query_id else None

    logger.info(
        "Fetching items from Trade API",
        game=game.value,
        num_ids=len(result_ids[:10]),
        has_query_id=query_id is not None,
    )

    try:
        client = get_http_client()
        response = await client.get(fetch_url, params=params)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        # Extract results
        items: list[dict[str, Any]] = data.get("result", [])

        logger.info(
            "Trade fetch complete",
            num_items=len(items),
        )

        return items

    except Exception as e:
        logger.error(
            "Trade fetch failed",
            game=game.value,
            num_ids=len(result_ids),
            error=str(e),
        )
        raise


async def search_and_fetch_items(
    game: Game,
    league: str,
    query: dict[str, Any],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Convenience function to search and fetch in one call.

    This is the primary entry point for most use cases.

    Args:
        game: Game context
        league: League name
        query: Trade API query
        limit: Max results (default: 10)

    Returns:
        List of full item details

    Example:
        >>> query = build_simple_query("Jade Amulet", min_life=60)
        >>> items = await search_and_fetch_items(Game.POE1, "Standard", query)
        >>> for item in items:
        ...     print(item['item']['name'], item['listing']['price'])
    """
    logger.info(
        "Starting search and fetch",
        game=game.value,
        league=league,
        limit=limit,
    )

    # Step 1: Search for item IDs
    result_ids = await search_items(game, league, query, limit)

    if not result_ids:
        logger.warning("No results found")
        return []

    # Step 2: Fetch item details
    items = await fetch_items(game, result_ids)

    logger.info(
        "Search and fetch complete",
        total_items=len(items),
    )

    return items


def build_simple_query(
    item_type: str,
    min_life: int | None = None,
    max_price_chaos: int | None = None,
    online_only: bool = True,
) -> dict[str, Any]:
    """Build a simple Trade API query (MVP version).

    Phase 1: Minimal query builder for basic searches.
    Future: Expand with more filters, stat types, etc.

    Args:
        item_type: Base type name (e.g., "Jade Amulet", "Siege Axe")
        min_life: Minimum life requirement
        max_price_chaos: Maximum price in chaos orbs
        online_only: Only show items from online sellers (default: True)

    Returns:
        Trade API query structure

    Example:
        >>> query = build_simple_query("Jade Amulet", min_life=60, max_price_chaos=50)
        >>> result_ids = await search_items(Game.POE1, "Standard", query)
    """
    query: dict[str, Any] = {
        "query": {
            "status": {"option": "online" if online_only else "any"},
            "type": item_type,
            "filters": {},
        },
        "sort": {"price": "asc"},  # Cheapest first
    }

    # Add stat filters if provided
    stat_filters = []
    if min_life is not None:
        stat_filters.append(
            {
                "id": "pseudo.pseudo_total_life",
                "value": {"min": min_life},
            }
        )

    if stat_filters:
        query["query"]["stats"] = [
            {
                "type": "and",
                "filters": stat_filters,
            }
        ]

    # Add price filter if provided
    if max_price_chaos is not None:
        query["query"]["filters"]["trade_filters"] = {
            "filters": {
                "price": {
                    "max": max_price_chaos,
                }
            }
        }

    return query


# Adapter retained for testability/backwards compatibility
def get_http_client():
    """Return a PoE-configured HTTP client.

    Kept as a separate function so test suites can monkeypatch/magicmock easily.
    """
    return create_poe_http_client()
