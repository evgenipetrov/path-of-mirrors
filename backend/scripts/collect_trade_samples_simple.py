#!/usr/bin/env python3
"""
Simple trade API sample collector based on v0.4 working code.

Collects minimal samples for model design - just enough to understand the structure.
"""

import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger()

# Your POESESSID cookie
POESESSID = "611483df474ee9ffa571a19c513527c2"

# Rate limiting (conservative)
RATE_LIMIT_DELAY = 3.0  # 3 seconds between requests


async def collect_sample(
    client: httpx.AsyncClient,
    game: str,
    league: str,
    category: str,
    rarity: str,
) -> dict:
    """Collect a single trade sample."""
    # Build API URL
    api_base = "/api/trade2" if game == "poe2" else "/api/trade"
    search_url = f"https://www.pathofexile.com{api_base}/search/{league}"

    # Build query payload (based on v0.4 working code)
    payload = {
        "query": {
            "status": {"option": "online"},
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "type_filters": {
                    "filters": {
                        "category": {"option": category},
                        "rarity": {"option": rarity},
                    }
                }
            },
        },
        "sort": {"price": "asc"},
        "engine": "new",
    }

    headers = {
        "Cookie": f"POESESSID={POESESSID}",
        "User-Agent": "PathOfMirrors/1.0 (Sample Collection)",
    }

    log.info(
        "executing_search",
        game=game,
        league=league,
        category=category,
        rarity=rarity,
    )

    try:
        # Step 1: Search
        response = await client.post(search_url, json=payload, headers=headers)
        response.raise_for_status()
        search_data = response.json()

        # Check rate limit headers
        rate_headers = {
            "x-rate-limit-account": response.headers.get("x-rate-limit-account"),
            "x-rate-limit-account-state": response.headers.get("x-rate-limit-account-state"),
            "x-rate-limit-ip": response.headers.get("x-rate-limit-ip"),
            "x-rate-limit-ip-state": response.headers.get("x-rate-limit-ip-state"),
            "retry-after": response.headers.get("retry-after"),
        }

        log.info("rate_limit_info", **{k: v for k, v in rate_headers.items() if v})

        # Get first 10 result IDs
        result_ids = search_data.get("result", [])[:10]
        query_id = search_data.get("id")

        if not result_ids:
            log.warning("no_results", game=game, league=league, category=category)
            return {
                "search": search_data,
                "items": None,
                "metadata": {
                    "game": game,
                    "league": league,
                    "category": category,
                    "rarity": rarity,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "empty",
                },
            }

        log.info("search_success", total_results=len(search_data.get("result", [])), fetching=len(result_ids))

        # Step 2: Fetch (respect rate limit)
        await asyncio.sleep(RATE_LIMIT_DELAY)

        ids_str = ",".join(result_ids)
        fetch_url = f"https://www.pathofexile.com{api_base}/fetch/{ids_str}"
        params = {"query": query_id}

        response = await client.get(fetch_url, params=params, headers=headers)
        response.raise_for_status()
        items_data = response.json()

        log.info("fetch_success", items_fetched=len(items_data.get("result", [])))

        return {
            "search": search_data,
            "items": items_data,
            "metadata": {
                "game": game,
                "league": league,
                "category": category,
                "rarity": rarity,
                "query_payload": payload,
                "collected_at": datetime.now(UTC).isoformat(),
                "status": "success",
                "rate_limit_headers": rate_headers,
            },
        }

    except httpx.HTTPStatusError as e:
        log.error(
            "http_error",
            status_code=e.response.status_code,
            game=game,
            league=league,
            error=str(e),
        )
        return {
            "metadata": {
                "game": game,
                "league": league,
                "category": category,
                "rarity": rarity,
                "collected_at": datetime.now(UTC).isoformat(),
                "status": "failed",
                "error": f"HTTP {e.response.status_code}",
            },
        }


async def main():
    """Collect minimal trade samples for both games."""

    # Minimal sample configuration - targeting current temp leagues
    samples_config = [
        # PoE1 - Keepers of the Trove (current temp league)
        {"game": "poe1", "league": "Keepers", "category": "accessory.amulet", "rarity": "rare"},
        {"game": "poe1", "league": "Keepers", "category": "weapon.onesword", "rarity": "unique"},
        # PoE2 - Rise of the Abyssal (current temp league)
        {"game": "poe2", "league": "Rise of the Abyssal", "category": "accessory.amulet", "rarity": "rare"},
        {"game": "poe2", "league": "Rise of the Abyssal", "category": "weapon.onesword", "rarity": "unique"},
    ]

    output_dir = Path("../_samples/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("starting_collection", total_samples=len(samples_config))

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, config in enumerate(samples_config, 1):
            log.info("collecting_sample", num=i, total=len(samples_config), **config)

            sample_data = await collect_sample(client, **config)

            # Save sample
            league_dir = config["league"].lower().replace(" ", "_")
            game_dir = output_dir / config["game"] / "trade" / league_dir
            game_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{config['rarity']}_{config['category'].replace('.', '_')}.json"
            filepath = game_dir / filename

            with open(filepath, "w") as f:
                json.dump(sample_data, f, indent=2)

            log.info("sample_saved", path=str(filepath))

            # Rate limit between samples
            if i < len(samples_config):
                log.info("rate_limit_delay", seconds=RATE_LIMIT_DELAY)
                await asyncio.sleep(RATE_LIMIT_DELAY)

    log.info("collection_complete", total_samples=len(samples_config))


if __name__ == "__main__":
    asyncio.run(main())
