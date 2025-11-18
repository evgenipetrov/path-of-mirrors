#!/usr/bin/env python3
"""
Collect data samples from Path of Exile Trade API.

Usage:
    uv run python scripts/collect_trade_samples.py --game poe1
    uv run python scripts/collect_trade_samples.py --game poe2
    uv run python scripts/collect_trade_samples.py --all
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import structlog

log = structlog.get_logger()

# Current leagues
POE1_LEAGUES = ["Standard", "Settlers"]
POE2_LEAGUES = ["Standard"]

# Sample item types to search for
SAMPLE_SEARCHES = [
    {"name": "unique_weapon", "query": {"type": "unique", "category": "weapon"}},
    {"name": "unique_armour", "query": {"type": "unique", "category": "armour"}},
    {"name": "rare_weapon", "query": {"rarity": "rare", "category": "weapon"}},
    {"name": "currency", "query": {"type": "currency"}},
    {"name": "map", "query": {"type": "map"}},
    {"name": "gem", "query": {"type": "gem"}},
]

# Bulk exchange examples
BULK_EXCHANGES = [
    {"name": "chaos_divine", "have": "chaos", "want": "divine"},
    {"name": "exalt_divine", "have": "exalt", "want": "divine"},
]


class TradeSampleCollector:
    """Collect samples from official trade API."""

    def __init__(self, game: str):
        self.game = game
        if game == "poe1":
            self.base_url = "https://www.pathofexile.com/api/trade"
            self.leagues = POE1_LEAGUES
        elif game == "poe2":
            # TODO: Verify actual PoE2 trade endpoint
            self.base_url = "https://www.pathofexile.com/api/trade2"
            self.leagues = POE2_LEAGUES
        else:
            raise ValueError(f"Invalid game: {game}")

        self.output_dir = Path(f"../_samples/data/{game}/trade")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.samples: list[dict[str, Any]] = []

    async def collect_all(self) -> None:
        """Collect all trade API samples."""
        log.info("starting_collection", game=self.game)

        async with httpx.AsyncClient(timeout=30.0) as client:
            for league in self.leagues:
                # Collect item searches
                for search in SAMPLE_SEARCHES:
                    await self._collect_search_sample(client, league, search)
                    await asyncio.sleep(2.0)  # Respect rate limits

                # Collect bulk exchanges
                for exchange in BULK_EXCHANGES:
                    await self._collect_bulk_sample(client, league, exchange)
                    await asyncio.sleep(2.0)

        self._save_metadata()
        log.info("collection_complete", samples=len(self.samples))

    async def _collect_search_sample(
        self,
        client: httpx.AsyncClient,
        league: str,
        search: dict[str, Any],
    ) -> None:
        """Collect an item search sample."""
        # TODO: Implement actual trade API search
        # This requires constructing proper query JSON
        # See: https://www.pathofexile.com/developer/docs/reference
        log.warning(
            "trade_search_not_implemented",
            league=league,
            search_name=search["name"],
        )
        pass

    async def _collect_bulk_sample(
        self,
        client: httpx.AsyncClient,
        league: str,
        exchange: dict[str, Any],
    ) -> None:
        """Collect a bulk exchange sample."""
        # TODO: Implement bulk exchange API
        log.warning(
            "bulk_exchange_not_implemented",
            league=league,
            exchange_name=exchange["name"],
        )
        pass

    def _save_metadata(self) -> None:
        """Save metadata."""
        meta = {
            "source": "trade_api",
            "game": self.game,
            "collected_at": datetime.utcnow().isoformat() + "Z",
            "collector_version": "1.0",
            "notes": "Trade API samples - IMPLEMENTATION PENDING",
            "samples": self.samples,
        }

        with open(self.output_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect trade API samples")
    parser.add_argument(
        "--game",
        choices=["poe1", "poe2", "all"],
        default="all",
    )
    args = parser.parse_args()

    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        collector = TradeSampleCollector(game)
        await collector.collect_all()


if __name__ == "__main__":
    asyncio.run(main())
