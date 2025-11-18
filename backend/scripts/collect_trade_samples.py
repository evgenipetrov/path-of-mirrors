#!/usr/bin/env python3
"""
Collect data samples from Path of Exile Trade API for both PoE1 and PoE2.

The Trade API has stricter rate limits than poe.ninja, so we collect representative samples:
- Item search results (unique items, rare items with mods, currency, maps, gems)
- Bulk exchange results (currency trading)
- Detailed item data (full modifier lists)

Rate limits (as of 2024):
- Search endpoint: ~1 request per second
- Fetch endpoint: ~1 request per second
- Requires POESESSID cookie for authentication

Usage:
    # Set your POESESSID cookie
    export POESESSID="your_cookie_here"

    # Collect samples
    uv run python scripts/collect_trade_samples.py --game poe1 --poesessid YOUR_COOKIE
    uv run python scripts/collect_trade_samples.py --game poe2 --poesessid YOUR_COOKIE
    uv run python scripts/collect_trade_samples.py --all --poesessid YOUR_COOKIE
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import httpx
import structlog

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure import get_global_config

log = structlog.get_logger()

# Load configuration
GLOBAL_CONFIG = get_global_config()

# Trade API configuration
TRADE_API_BASE = "https://www.pathofexile.com/api/trade"
RATE_LIMIT_DELAY = 2.0  # Seconds between requests (very conservative to avoid 429)
ITEMS_PER_SEARCH = 10  # Number of items to fetch per search
MAX_SEARCHES_PER_CATEGORY = 1  # Only 1 attempt per category to avoid rate limits


class TradeAPISampleCollector:
    """Collect samples from Path of Exile Trade API."""

    def __init__(self, game: str, poesessid: str | None = None):
        self.game = game
        self.game_key = game.lower()

        # Get configuration
        if self.game_key == "poe1":
            self.leagues = GLOBAL_CONFIG.poe1.leagues
            self.trade_base = TRADE_API_BASE
        elif self.game_key == "poe2":
            self.leagues = GLOBAL_CONFIG.poe2.leagues
            # PoE2 uses /trade2 endpoint
            self.trade_base = f"{TRADE_API_BASE}2"
        else:
            raise ValueError(f"Invalid game: {game}")

        # Authentication
        self.poesessid = poesessid or os.getenv("POESESSID")
        if not self.poesessid:
            log.warning(
                "no_poesessid_provided",
                message="Some endpoints may fail without authentication. Set POESESSID env var or pass --poesessid",
            )

        # Output directories
        self.output_dir = Path(f"../_samples/data/{self.game_key}/trade")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metadata
        self.samples: list[dict[str, Any]] = []

        # Sample search configurations
        self.search_configs = self._get_search_configs()

    def _get_search_configs(self) -> dict[str, dict[str, Any]]:
        """Define search configurations for different item types.

        Minimal set - just 2 representative queries per game to show structure.
        """
        if self.game_key == "poe1":
            return {
                "rare_amulet": {
                    "query": {
                        "status": {"option": "online"},
                        "stats": [{"type": "and", "filters": []}],
                        "filters": {
                            "type_filters": {
                                "filters": {
                                    "category": {"option": "accessory.amulet"},
                                    "rarity": {"option": "rare"},
                                }
                            }
                        },
                    },
                    "sort": {"price": "asc"},
                },
                "unique_weapon_sword": {
                    "query": {
                        "status": {"option": "online"},
                        "stats": [{"type": "and", "filters": []}],
                        "filters": {
                            "type_filters": {
                                "filters": {
                                    "category": {"option": "weapon.onesword"},
                                    "rarity": {"option": "unique"},
                                }
                            }
                        },
                    },
                    "sort": {"price": "asc"},
                },
            }
        else:  # PoE2
            return {
                "rare_amulet": {
                    "query": {
                        "status": {"option": "online"},
                        "stats": [{"type": "and", "filters": []}],
                        "filters": {
                            "type_filters": {
                                "filters": {
                                    "category": {"option": "accessory.amulet"},
                                    "rarity": {"option": "rare"},
                                }
                            }
                        },
                    },
                    "sort": {"price": "asc"},
                },
                "unique_weapon_sword": {
                    "query": {
                        "status": {"option": "online"},
                        "stats": [{"type": "and", "filters": []}],
                        "filters": {
                            "type_filters": {
                                "filters": {
                                    "category": {"option": "weapon.onesword"},
                                    "rarity": {"option": "unique"},
                                }
                            }
                        },
                    },
                    "sort": {"price": "asc"},
                },
            }

    async def collect_all(self) -> None:
        """Collect all trade API samples.

        Minimal collection: Only Standard league, limited searches to avoid rate limits.
        """
        log.info(
            "starting_trade_collection",
            game=self.game,
            leagues_available=self.leagues,
            collecting_only="Standard",
            search_types=list(self.search_configs.keys()),
        )

        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            # Only collect Standard league to minimize API calls
            standard_league = "Standard"

            # Collect item search samples
            await self._collect_league_samples(client, standard_league)

            # Collect one bulk exchange sample
            await self._collect_bulk_samples(client, standard_league)

        # Save metadata
        self._save_metadata()

        log.info(
            "trade_collection_complete",
            game=self.game,
            samples_collected=len(self.samples),
        )

    async def _collect_league_samples(
        self, client: httpx.AsyncClient, league: str
    ) -> None:
        """Collect item search samples for a league."""
        log.info("collecting_league_samples", league=league)

        for search_name, search_config in self.search_configs.items():
            # Limit searches per category
            for attempt in range(MAX_SEARCHES_PER_CATEGORY):
                try:
                    await self._collect_search_sample(
                        client, league, search_name, search_config, attempt
                    )
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    break  # Success, move to next search
                except Exception as e:
                    log.error(
                        "search_failed",
                        league=league,
                        search_name=search_name,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    if attempt < MAX_SEARCHES_PER_CATEGORY - 1:
                        await asyncio.sleep(RATE_LIMIT_DELAY * 2)  # Back off

    async def _collect_search_sample(
        self,
        client: httpx.AsyncClient,
        league: str,
        search_name: str,
        search_config: dict[str, Any],
        attempt: int,
    ) -> None:
        """Collect a single search sample with item details."""
        log.info(
            "executing_search",
            league=league,
            search_name=search_name,
            attempt=attempt + 1,
        )

        # Step 1: Execute search to get result IDs
        search_url = f"{self.trade_base}/search/{league}"
        response = await client.post(search_url, json=search_config)
        response.raise_for_status()
        search_data = response.json()

        # Extract result IDs
        result_ids = search_data.get("result", [])[:ITEMS_PER_SEARCH]
        query_id = search_data.get("id")

        if not result_ids:
            log.warning(
                "no_search_results",
                league=league,
                search_name=search_name,
            )
            self.samples.append({
                "type": "item_search",
                "league": league,
                "search_name": search_name,
                "attempt": attempt,
                "collected_at": datetime.now(UTC).isoformat(),
                "status": "empty",
                "message": "No results found",
            })
            return

        log.info(
            "search_results_found",
            league=league,
            search_name=search_name,
            total_results=len(search_data.get("result", [])),
            fetching_count=len(result_ids),
        )

        # Step 2: Fetch detailed item data
        await asyncio.sleep(RATE_LIMIT_DELAY)

        fetch_url = f"{self.trade_base}/fetch/{','.join(result_ids)}"
        params = {"query": query_id} if query_id else {}

        response = await client.get(fetch_url, params=params)
        response.raise_for_status()
        items_data = response.json()

        # Save combined search + fetch results
        output_dir = self.output_dir / league.lower().replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)

        combined_data = {
            "search": search_data,
            "items": items_data,
            "metadata": {
                "search_name": search_name,
                "search_config": search_config,
                "league": league,
                "collected_at": datetime.now(UTC).isoformat(),
            },
        }

        filename = f"search_{search_name}_attempt{attempt}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(combined_data, f, indent=2)

        self.samples.append({
            "filename": str(filepath.relative_to(self.output_dir)),
            "type": "item_search",
            "league": league,
            "search_name": search_name,
            "attempt": attempt,
            "query_id": query_id,
            "total_results": len(search_data.get("result", [])),
            "fetched_items": len(items_data.get("result", [])),
            "size_bytes": filepath.stat().st_size,
            "collected_at": datetime.now(UTC).isoformat(),
            "status": "success",
        })

        log.info(
            "search_sample_collected",
            filename=filename,
            items_fetched=len(items_data.get("result", [])),
        )

    async def _collect_bulk_samples(
        self, client: httpx.AsyncClient, league: str
    ) -> None:
        """Collect bulk exchange samples for a league."""
        log.info("collecting_bulk_samples", league=league)

        # Bulk exchange queries (just one sample per game)
        if self.game_key == "poe1":
            bulk_configs = [
                {
                    "name": "chaos_for_divine",
                    "exchange": {
                        "status": {"option": "online"},
                        "have": ["chaos"],
                        "want": ["divine"],
                    },
                },
            ]
        else:  # PoE2
            bulk_configs = [
                {
                    "name": "exalt_for_divine",
                    "exchange": {
                        "status": {"option": "online"},
                        "have": ["exalted"],
                        "want": ["divine"],
                    },
                },
            ]

        for bulk_config in bulk_configs:
            try:
                await self._collect_bulk_sample(client, league, bulk_config)
                await asyncio.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                log.error(
                    "bulk_search_failed",
                    league=league,
                    bulk_name=bulk_config["name"],
                    error=str(e),
                )

    async def _collect_bulk_sample(
        self,
        client: httpx.AsyncClient,
        league: str,
        bulk_config: dict[str, Any],
    ) -> None:
        """Collect a single bulk exchange sample."""
        bulk_name = bulk_config["name"]
        log.info("executing_bulk_search", league=league, bulk_name=bulk_name)

        # Execute bulk exchange search
        exchange_url = f"{self.trade_base}/exchange/{league}"
        response = await client.post(exchange_url, json=bulk_config["exchange"])
        response.raise_for_status()
        exchange_data = response.json()

        # Extract result IDs
        result_ids = exchange_data.get("result", [])[:ITEMS_PER_SEARCH]
        query_id = exchange_data.get("id")

        if not result_ids:
            log.warning("no_bulk_results", league=league, bulk_name=bulk_name)
            self.samples.append({
                "type": "bulk_exchange",
                "league": league,
                "bulk_name": bulk_name,
                "collected_at": datetime.now(UTC).isoformat(),
                "status": "empty",
                "message": "No results found",
            })
            return

        # Fetch detailed exchange listings
        await asyncio.sleep(RATE_LIMIT_DELAY)

        fetch_url = f"{self.trade_base}/fetch/{','.join(result_ids)}"
        params = {"query": query_id, "exchange": ""}  # exchange flag for bulk

        response = await client.get(fetch_url, params=params)
        response.raise_for_status()
        listings_data = response.json()

        # Save combined results
        output_dir = self.output_dir / league.lower().replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)

        combined_data = {
            "exchange": exchange_data,
            "listings": listings_data,
            "metadata": {
                "bulk_name": bulk_name,
                "bulk_config": bulk_config["exchange"],
                "league": league,
                "collected_at": datetime.now(UTC).isoformat(),
            },
        }

        filename = f"bulk_{bulk_name}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(combined_data, f, indent=2)

        self.samples.append({
            "filename": str(filepath.relative_to(self.output_dir)),
            "type": "bulk_exchange",
            "league": league,
            "bulk_name": bulk_name,
            "query_id": query_id,
            "total_results": len(exchange_data.get("result", [])),
            "fetched_listings": len(listings_data.get("result", [])),
            "size_bytes": filepath.stat().st_size,
            "collected_at": datetime.now(UTC).isoformat(),
            "status": "success",
        })

        log.info(
            "bulk_sample_collected",
            filename=filename,
            listings_fetched=len(listings_data.get("result", [])),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authentication."""
        headers = {
            "User-Agent": "PathOfMirrors/1.0 (Data Sample Collection)",
        }

        if self.poesessid:
            headers["Cookie"] = f"POESESSID={self.poesessid}"

        return headers

    def _save_metadata(self) -> None:
        """Save collection metadata to meta.json."""
        meta = {
            "source": "pathofexile.com/trade",
            "game": self.game,
            "collected_at": datetime.now(UTC).isoformat(),
            "collector_version": "1.0",
            "config": {
                "leagues": self.leagues,
                "trade_base_url": self.trade_base,
                "rate_limit_delay": RATE_LIMIT_DELAY,
                "items_per_search": ITEMS_PER_SEARCH,
                "search_types": list(self.search_configs.keys()),
                "authenticated": bool(self.poesessid),
            },
            "samples": self.samples,
        }

        meta_path = self.output_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        log.info("metadata_saved", path=str(meta_path), total_samples=len(self.samples))


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect Path of Exile Trade API samples"
    )
    parser.add_argument(
        "--game",
        choices=["poe1", "poe2", "all"],
        default="all",
        help="Which game to collect samples for",
    )
    parser.add_argument(
        "--poesessid",
        type=str,
        help="POESESSID cookie for authentication (or set POESESSID env var)",
    )
    args = parser.parse_args()

    # Print warning about rate limits
    log.warning(
        "trade_api_rate_limits",
        message="Trade API has strict rate limits. This script respects them with delays.",
        rate_limit_delay=RATE_LIMIT_DELAY,
        estimated_time_per_league="~2-3 minutes",
    )

    # Determine games to collect
    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        collector = TradeAPISampleCollector(game, poesessid=args.poesessid)
        await collector.collect_all()


if __name__ == "__main__":
    asyncio.run(main())
