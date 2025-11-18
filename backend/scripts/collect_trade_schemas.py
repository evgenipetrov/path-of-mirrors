#!/usr/bin/env python3
"""
Collect Trade API schema endpoints (filters, stats, static, items, leagues).

These schemas provide:
- stats: The "Rosetta Stone" for translating stat IDs to human-readable text
- filters: Available filter types and options for search queries
- items: Item type categories and bases
- static: Static data like currency types
- leagues: Active leagues list
"""

import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger()

# Schema endpoints from v0.4 code
SCHEMA_ENDPOINTS = {
    "poe1": {
        "filters": "/api/trade/data/filters",
        "stats": "/api/trade/data/stats",
        "static": "/api/trade/data/static",
        "items": "/api/trade/data/items",
        "leagues": "/api/trade/data/leagues",
    },
    "poe2": {
        "filters": "/api/trade2/data/filters",
        "stats": "/api/trade2/data/stats",
        "static": "/api/trade2/data/static",
        "items": "/api/trade2/data/items",
        "leagues": "/api/trade2/data/leagues",
    },
}

BASE_URL = "https://www.pathofexile.com"

# POESESSID cookie (same as used for trade search)
POESESSID = "611483df474ee9ffa571a19c513527c2"


async def collect_schemas(client: httpx.AsyncClient, game: str) -> dict:
    """Collect all schema endpoints for a game."""
    endpoints = SCHEMA_ENDPOINTS[game]
    schemas = {}

    for name, path in endpoints.items():
        url = f"{BASE_URL}{path}"
        log.info("fetching_schema", game=game, name=name, url=url)

        try:
            headers = {"Cookie": f"POESESSID={POESESSID}"}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            schemas[name] = response.json()
            log.info("schema_fetched", game=game, name=name, size=len(response.content))
        except httpx.HTTPStatusError as e:
            log.error("schema_fetch_failed", game=game, name=name, status=e.response.status_code)
            schemas[name] = {"error": str(e), "status_code": e.response.status_code}

        # Small delay between requests (not rate limited like search, but be polite)
        await asyncio.sleep(0.5)

    return schemas


async def main():
    """Collect Trade API schemas for both games."""
    output_dir = Path("../_samples/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("starting_schema_collection")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for game in ["poe1", "poe2"]:
            log.info("collecting_game_schemas", game=game)

            schemas = await collect_schemas(client, game)

            # Save to game-specific directory
            game_dir = output_dir / game / "trade"
            game_dir.mkdir(parents=True, exist_ok=True)

            filepath = game_dir / "schemas.json"
            with open(filepath, "w") as f:
                json.dump(
                    {
                        "schemas": schemas,
                        "metadata": {
                            "game": game,
                            "collected_at": datetime.now(UTC).isoformat(),
                            "source": "pathofexile.com Trade API",
                        },
                    },
                    f,
                    indent=2,
                )

            log.info("schemas_saved", game=game, path=str(filepath))

    log.info("schema_collection_complete")


if __name__ == "__main__":
    asyncio.run(main())
