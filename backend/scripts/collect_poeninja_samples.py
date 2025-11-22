#!/usr/bin/env python3
"""
Collect data samples from poe.ninja API for both PoE1 and PoE2.

Collects three types of data:
1. Economy data (item/currency prices)
2. Build data (character builds from ladder)
3. Index state (metadata about snapshots)

Usage:
    uv run python scripts/collect_poeninja_samples.py --game poe1 --type economy
    uv run python scripts/collect_poeninja_samples.py --game poe1 --type builds
    uv run python scripts/collect_poeninja_samples.py --game poe1 --type all
    uv run python scripts/collect_poeninja_samples.py --all
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Add scripts dir for proto module
sys.path.insert(0, str(Path(__file__).parent))

from poeninja_proto import parse_build_search_payload

from infrastructure import get_global_config, get_poeninja_config

log = structlog.get_logger()

# Load configuration
GLOBAL_CONFIG = get_global_config()
POENINJA_CONFIG = get_poeninja_config()


class PoeNinjaSampleCollector:
    """Collect samples from poe.ninja API."""

    def __init__(self, game: str):
        self.game = game
        self.game_key = game.lower()

        # Get configuration
        if self.game_key == "poe1":
            self.economy_base_url = POENINJA_CONFIG.base_url_economy_poe1
            self.builds_base_url = POENINJA_CONFIG.base_url_builds_poe1
            self.index_state_url = POENINJA_CONFIG.base_url_index_state_poe1
            self.leagues = GLOBAL_CONFIG.poe1.leagues
            self.economy_categories = POENINJA_CONFIG.poe1_economy_categories
        elif self.game_key == "poe2":
            self.economy_base_url = POENINJA_CONFIG.base_url_economy_poe2
            self.builds_base_url = POENINJA_CONFIG.base_url_builds_poe2
            self.index_state_url = POENINJA_CONFIG.base_url_index_state_poe2
            self.leagues = GLOBAL_CONFIG.poe2.leagues
            self.economy_categories = POENINJA_CONFIG.poe2_economy_categories
        else:
            raise ValueError(f"Invalid game: {game}")

        # Output directories
        self.output_dir = Path(f"../_samples/data/{self.game_key}/poeninja")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metadata
        self.samples: list[dict[str, Any]] = []

    async def collect_all(self, data_types: list[str]) -> None:
        """Collect all requested data types."""
        log.info(
            "starting_collection",
            game=self.game,
            leagues=self.leagues,
            data_types=data_types,
        )

        async with httpx.AsyncClient(timeout=POENINJA_CONFIG.timeout) as client:
            if "economy" in data_types:
                await self.collect_economy_data(client)

            if "builds" in data_types:
                await self.collect_build_data(client)

            if "index_state" in data_types or "all" in data_types:
                await self.collect_index_state(client)

        # Save metadata
        self._save_metadata(data_types)

        log.info(
            "collection_complete",
            game=self.game,
            samples_collected=len(self.samples),
        )

    async def collect_economy_data(self, client: httpx.AsyncClient) -> None:
        """Collect economy snapshots for all leagues and categories."""
        log.info("collecting_economy_data", leagues=self.leagues)

        # Validate league names against index-state
        validated_leagues = await self._validate_league_names(client, self.leagues)

        for league in validated_leagues:
            for endpoint_type, categories in self.economy_categories.items():
                for category in categories:
                    await self._collect_economy_snapshot(client, league, endpoint_type, category)
                    await asyncio.sleep(POENINJA_CONFIG.rate_limit)

    async def collect_build_data(self, client: httpx.AsyncClient) -> None:
        """Collect build samples from ladder."""
        log.info("collecting_build_data", limit=POENINJA_CONFIG.build_sample_limit)

        # First, get index-state to find snapshot versions
        try:
            index_state = await self._fetch_json(client, self.index_state_url)
            snapshot_versions = index_state.get("snapshotVersions", [])
            if not snapshot_versions:
                log.warning("no_snapshot_versions_found", skipping_builds=True)
                return
        except Exception as e:
            log.error("failed_to_fetch_index_state", error=str(e), skipping_builds=True)
            return

        # Validate league names
        validated_leagues = await self._validate_league_names(client, self.leagues)

        # For each league, find matching snapshot version
        for league in validated_leagues:
            # Find snapshot version for this league
            # Try matching by league name or URL
            snapshot_version = None
            snapshot_url_slug = None
            snapshot_name_slug = None

            for snapshot in snapshot_versions:
                # Match by name or URL (case-insensitive)
                snapshot_name = snapshot.get("name", "").lower()
                snapshot_url = snapshot.get("url", "").lower()
                league_lower = league.lower()

                # Try exact match first
                if snapshot_name == league_lower or snapshot_url == league_lower:
                    snapshot_version = snapshot.get("version")
                    snapshot_url_slug = snapshot.get("url")
                    snapshot_name_slug = snapshot.get("snapshotName") or snapshot.get(
                        "name", ""
                    ).lower().replace(" ", "-")
                    if snapshot_version:
                        log.info(
                            "found_snapshot_version",
                            league=league,
                            snapshot_name=snapshot.get("name"),
                            snapshot_url=snapshot_url_slug,
                            snapshot_name_slug=snapshot_name_slug,
                            version=snapshot_version,
                        )
                        break

                # Try partial match (for leagues like "Rise of the Abyssal" vs "abyss")
                if league_lower in snapshot_name or snapshot_url in league_lower:
                    snapshot_version = snapshot.get("version")
                    snapshot_url_slug = snapshot.get("url")
                    snapshot_name_slug = snapshot.get("snapshotName") or snapshot.get(
                        "name", ""
                    ).lower().replace(" ", "-")
                    if snapshot_version:
                        log.info(
                            "found_snapshot_version_partial",
                            league=league,
                            snapshot_name=snapshot.get("name"),
                            snapshot_url=snapshot_url_slug,
                            snapshot_name_slug=snapshot_name_slug,
                            version=snapshot_version,
                        )
                        break

            if not snapshot_version:
                log.warning(
                    "no_snapshot_version_for_league",
                    league=league,
                    skipping_league=True,
                )
                continue

            await self._collect_build_samples(
                client, league, snapshot_version, snapshot_url_slug, snapshot_name_slug
            )
            await asyncio.sleep(POENINJA_CONFIG.rate_limit)

    async def collect_index_state(self, client: httpx.AsyncClient) -> None:
        """Collect index state metadata."""
        log.info("collecting_index_state")

        try:
            data = await self._fetch_json(client, self.index_state_url)

            # Save to file
            output_dir = self.output_dir / "index_state"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            filename = f"index_state_{timestamp}.json"
            filepath = output_dir / filename

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self.samples.append(
                {
                    "filename": filename,
                    "type": "index_state",
                    "size_bytes": filepath.stat().st_size,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "success",
                }
            )

            log.info("index_state_collected", filename=filename)

        except Exception as e:
            log.error("index_state_error", error=str(e))
            self.samples.append(
                {
                    "type": "index_state",
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "failed",
                    "error": str(e),
                }
            )

    async def _collect_economy_snapshot(
        self,
        client: httpx.AsyncClient,
        league: str,
        endpoint_type: str,
        category: str,
    ) -> None:
        """Collect a single economy snapshot."""
        # Build URL based on endpoint type
        if endpoint_type == "exchange":
            url = f"{self.economy_base_url}/exchange/current/overview"
        elif endpoint_type == "item":
            url = f"{self.economy_base_url}/stash/current/item/overview"
        else:
            log.error("invalid_endpoint_type", endpoint_type=endpoint_type)
            return

        params = {"league": league, "type": category}

        log.info(
            "fetching_economy_sample",
            league=league,
            endpoint_type=endpoint_type,
            category=category,
        )

        try:
            data = await self._fetch_json(client, url, params=params)

            # Check if data is empty
            item_count = len(data.get("lines", []))
            if item_count == 0:
                log.warning(
                    "empty_economy_data",
                    league=league,
                    category=category,
                    message="Received empty data - league name may be incorrect or no data available",
                )
                # Still record the attempt but mark as empty
                self.samples.append(
                    {
                        "type": "economy",
                        "league": league,
                        "endpoint_type": endpoint_type,
                        "category": category,
                        "url": f"{url}?{httpx.QueryParams(params)}",
                        "item_count": 0,
                        "collected_at": datetime.now(UTC).isoformat(),
                        "status": "empty",
                        "warning": "No items in response",
                    }
                )
                return  # Skip saving empty files

            # Save to file (only if we have data)
            output_dir = self.output_dir / "economy" / league.lower().replace(" ", "_")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{category.lower()}.json"
            filepath = output_dir / filename

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            # Add to metadata
            self.samples.append(
                {
                    "filename": str(filepath.relative_to(self.output_dir)),
                    "type": "economy",
                    "league": league,
                    "endpoint_type": endpoint_type,
                    "category": category,
                    "url": f"{url}?{httpx.QueryParams(params)}",
                    "item_count": item_count,
                    "size_bytes": filepath.stat().st_size,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "success",
                }
            )

            log.info(
                "economy_sample_collected",
                filename=filename,
                item_count=item_count,
            )

        except httpx.HTTPStatusError as e:
            log.warning(
                "http_error",
                league=league,
                category=category,
                status_code=e.response.status_code,
                error=str(e),
            )
            self.samples.append(
                {
                    "type": "economy",
                    "league": league,
                    "endpoint_type": endpoint_type,
                    "category": category,
                    "url": f"{url}?{httpx.QueryParams(params)}",
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "failed",
                    "error": f"HTTP {e.response.status_code}",
                }
            )

        except Exception as e:
            log.error(
                "unexpected_error",
                league=league,
                category=category,
                error=str(e),
            )
            self.samples.append(
                {
                    "type": "economy",
                    "league": league,
                    "endpoint_type": endpoint_type,
                    "category": category,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "failed",
                    "error": str(e),
                }
            )

    async def _collect_build_samples(
        self,
        client: httpx.AsyncClient,
        league: str,
        snapshot_version: str,
        snapshot_url_slug: str | None = None,
        snapshot_name_slug: str | None = None,
    ) -> None:
        """Collect build samples from ladder (protobuf-encoded)."""
        log.info(
            "fetching_build_search",
            league=league,
            snapshot_version=snapshot_version,
            overview_param=snapshot_name_slug,
        )

        # Fetch protobuf-encoded build search
        # The overview parameter should use the snapshot name slug (e.g., "rise-of-the-abyssal")
        search_url = f"{self.builds_base_url}/{snapshot_version}/search"
        params = {
            "overview": snapshot_name_slug or league.lower(),  # Use snapshot name slug
            # Note: PoE1 uses type=exp, PoE2 doesn't seem to need it based on sample config
        }

        # Add type=exp for PoE1 only
        if self.game_key == "poe1":
            params["type"] = "exp"

        try:
            # Fetch raw protobuf data
            response = await client.get(search_url, params=params)
            response.raise_for_status()
            # httpx response.content is already bytes
            raw_payload = bytes(response.content)

            # Decode protobuf
            parsed_data = parse_build_search_payload(raw_payload)

            # Debug: log parsed data
            log.info(
                "parsed_protobuf",
                num_summaries=len(parsed_data.summaries),
                payload_size=len(raw_payload),
            )

            # Create output directory
            output_dir = self.output_dir / "builds" / league.lower().replace(" ", "_")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save decoded search results as JSON
            search_data = {
                "summaries": [
                    {"account": s.account, "character": s.character} for s in parsed_data.summaries
                ],
                "snapshot_version": snapshot_version,
                "league": league,
                "overview": snapshot_name_slug or league.lower(),
            }
            search_filename = f"search_{snapshot_version}.json"
            search_path = output_dir / search_filename
            with open(search_path, "w") as f:
                json.dump(search_data, f, indent=2)

            # Save raw protobuf for reference
            proto_filename = f"search_{snapshot_version}.protobuf"
            proto_path = output_dir / proto_filename
            with open(proto_path, "wb") as f:
                f.write(raw_payload)

            # Get character details (limited sample)
            characters = parsed_data.summaries
            limit = min(len(characters), POENINJA_CONFIG.build_sample_limit)

            log.info(
                "collecting_character_details",
                total_found=len(characters),
                limit=limit,
            )

            for idx, build_summary in enumerate(characters[:limit]):
                await self._collect_character_detail(
                    client,
                    output_dir,
                    snapshot_version,
                    snapshot_name_slug or league.lower(),
                    build_summary.account,
                    build_summary.character,
                    idx,
                )
                await asyncio.sleep(POENINJA_CONFIG.rate_limit)

            self.samples.append(
                {
                    "filename": str(search_path.relative_to(self.output_dir)),
                    "type": "build_search",
                    "league": league,
                    "snapshot_version": snapshot_version,
                    "total_builds": len(characters),
                    "sampled_builds": limit,
                    "json_size_bytes": search_path.stat().st_size,
                    "protobuf_size_bytes": proto_path.stat().st_size,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "success",
                }
            )

        except Exception as e:
            import traceback

            log.error(
                "build_search_error", league=league, error=str(e), traceback=traceback.format_exc()
            )
            self.samples.append(
                {
                    "type": "build_search",
                    "league": league,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "failed",
                    "error": str(e),
                }
            )

    async def _collect_character_detail(
        self,
        client: httpx.AsyncClient,
        output_dir: Path,
        snapshot_version: str,
        overview_param: str,
        account: str,
        character: str,
        index: int,
    ) -> None:
        """Collect detailed character information."""
        url = f"{self.builds_base_url}/{snapshot_version}/character"
        params = {
            "account": account,
            "name": character,
            "overview": overview_param,
        }

        # Add type=exp for PoE1 only
        if self.game_key == "poe1":
            params["type"] = "exp"

        try:
            data = await self._fetch_json(client, url, params=params)

            # Save character data
            filename = f"character_{index:03d}_{account}_{character}.json"
            # Sanitize filename
            filename = "".join(c if c.isalnum() or c in ("_", "-", ".") else "_" for c in filename)
            filepath = output_dir / filename

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self.samples.append(
                {
                    "filename": str(filepath.relative_to(self.output_dir)),
                    "type": "character_detail",
                    "account": account,
                    "character": character,
                    "size_bytes": filepath.stat().st_size,
                    "collected_at": datetime.now(UTC).isoformat(),
                    "status": "success",
                }
            )

            log.info("character_collected", account=account, character=character)

        except Exception as e:
            log.warning(
                "character_fetch_error",
                account=account,
                character=character,
                error=str(e),
            )

    async def _fetch_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch JSON data from URL with error handling."""
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _validate_league_names(
        self,
        client: httpx.AsyncClient,
        leagues: list[str],
    ) -> list[str]:
        """Validate league names against index-state and suggest corrections."""
        try:
            index_state = await self._fetch_json(client, self.index_state_url)
            available_leagues = [league["name"] for league in index_state.get("economyLeagues", [])]

            if not available_leagues:
                log.warning("no_available_leagues_in_index_state")
                return leagues

            validated = []
            for league in leagues:
                if league in available_leagues:
                    validated.append(league)
                    log.info("league_validated", league=league)
                else:
                    # Try to find a close match
                    league_lower = league.lower()
                    matches = [
                        avail
                        for avail in available_leagues
                        if league_lower in avail.lower() or avail.lower() in league_lower
                    ]

                    if matches:
                        suggested = matches[0]
                        log.warning(
                            "league_name_corrected",
                            configured=league,
                            corrected_to=suggested,
                            available_leagues=available_leagues,
                        )
                        validated.append(suggested)
                    else:
                        log.error(
                            "league_not_found",
                            league=league,
                            available_leagues=available_leagues,
                        )
                        # Still try the original name
                        validated.append(league)

            return validated

        except Exception as e:
            log.warning(
                "league_validation_failed",
                error=str(e),
                using_configured_leagues=True,
            )
            return leagues

    def _save_metadata(self, data_types: list[str]) -> None:
        """Save collection metadata to meta.json."""
        total_economy_categories = sum(len(cats) for cats in self.economy_categories.values())

        meta = {
            "source": "poe.ninja",
            "game": self.game,
            "data_types": data_types,
            "collected_at": datetime.now(UTC).isoformat(),
            "collector_version": "2.1",
            "config": {
                "leagues": self.leagues,
                "economy_categories": total_economy_categories,
                "economy_endpoint_types": list(self.economy_categories.keys()),
                "build_sample_limit": POENINJA_CONFIG.build_sample_limit,
            },
            "samples": self.samples,
        }

        meta_path = self.output_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        log.info("metadata_saved", path=str(meta_path), total_samples=len(self.samples))


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect poe.ninja data samples")
    parser.add_argument(
        "--game",
        choices=["poe1", "poe2", "all"],
        default="all",
        help="Which game to collect samples for",
    )
    parser.add_argument(
        "--type",
        choices=["economy", "builds", "index_state", "all"],
        default="all",
        help="Type of data to collect",
    )
    args = parser.parse_args()

    # Print config summary
    poe1_total_categories = sum(
        len(cats) for cats in POENINJA_CONFIG.poe1_economy_categories.values()
    )
    poe2_total_categories = sum(
        len(cats) for cats in POENINJA_CONFIG.poe2_economy_categories.values()
    )

    log.info(
        "config_loaded",
        poe1_leagues=GLOBAL_CONFIG.poe1.leagues,
        poe2_leagues=GLOBAL_CONFIG.poe2.leagues,
        poe1_economy_categories=poe1_total_categories,
        poe2_economy_categories=poe2_total_categories,
        build_sample_limit=POENINJA_CONFIG.build_sample_limit,
        rate_limit=POENINJA_CONFIG.rate_limit,
    )

    # Determine data types to collect
    if args.type == "all":
        data_types = ["economy", "builds", "index_state"]
    else:
        data_types = [args.type]

    # Determine games to collect
    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        collector = PoeNinjaSampleCollector(game)
        await collector.collect_all(data_types)


if __name__ == "__main__":
    asyncio.run(main())
