#!/usr/bin/env python3
"""
Validate Currency domain model design against real sample data.

This script validates that the Currency model can correctly represent currencies
from poe.ninja economy data for both PoE1 and PoE2.

Usage:
    uv run python backend/scripts/validate_currency_design.py
    uv run python backend/scripts/validate_currency_design.py --game poe2
    uv run python backend/scripts/validate_currency_design.py --verbose

The validation logic demonstrates how to parse currency data from poe.ninja
and will be reused when implementing the poe.ninja adapter in Epic 1.4+.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Note: We don't import Currency class directly because it has SQLAlchemy dependencies.
# Instead, we validate the data structure requirements inline.
# This script validates that the Currency model design (game, name, display_name)
# can correctly represent currencies from poe.ninja data.


class ValidationResult:
    """Tracks validation results."""

    def __init__(self):
        self.results: list[tuple[str, str, str, str | None]] = []
        self.unique_currencies: set[str] = set()
        self.files_processed = 0

    def add_success(self, game: str, league: str, currency_name: str):
        """Record successful parsing."""
        self.results.append(("SUCCESS", game, league, currency_name, None))
        self.unique_currencies.add(currency_name)

    def add_failure(self, game: str, league: str, currency_name: str, error: str):
        """Record parsing failure."""
        self.results.append(("FAILED", game, league, currency_name, error))

    @property
    def successes(self):
        return [r for r in self.results if r[0] == "SUCCESS"]

    @property
    def failures(self):
        return [r for r in self.results if r[0] == "FAILED"]

    @property
    def success_rate(self) -> float:
        total = len(self.results)
        return (len(self.successes) / total * 100) if total > 0 else 0


def parse_poeninja_currency(
    currency_data: dict, game: str, league: str, result: ValidationResult
) -> None:
    """Parse currencies from poe.ninja economy data.

    poe.ninja format:
        {
          "core": {
            "items": [
              {
                "id": "chaos",
                "name": "Chaos Orb",
                "image": "/path/to/image.png",
                "category": "Currency",
                "detailsId": "chaos-orb"
              }
            ]
          },
          "lines": [
            {
              "id": "chaos",
              "primaryValue": 1.0,
              ...
            }
          ]
        }

    This function demonstrates the adapter logic for poe.ninja → Currency conversion.
    The Currency model stores only:
      - game (derived from context)
      - name (from "name" field)
      - display_name (derived from name - last word)

    Provider-specific fields (id, image, category) are NOT stored in core domain.
    """
    core_data = currency_data.get("core", {})
    items = core_data.get("items", [])

    for item in items:
        currency_name = item.get("name")
        if not currency_name:
            continue

        try:
            # Derive display_name from name (e.g., "Chaos Orb" -> "Chaos")
            # This is a simple heuristic - adapter can make it more sophisticated
            display_name = currency_name.split()[-1]

            # This simulates creating a Currency entity
            # In real adapter, this would use repository.create()
            currency = {
                "game": game,
                "name": currency_name,
                "display_name": display_name,
            }

            # Validate fields match Currency model requirements
            if not currency["game"] or not currency["name"] or not currency["display_name"]:
                raise ValueError("Missing required fields")

            result.add_success(game, league, currency_name)

        except Exception as e:
            result.add_failure(game, league, currency_name, str(e))


def validate_poeninja_currencies(
    game: str, result: ValidationResult, verbose: bool = False
) -> None:
    """Validate Currency against poe.ninja economy samples."""
    project_root = Path(__file__).parent.parent.parent
    economy_dir = project_root / f"_samples/data/{game}/poeninja/economy"

    if not economy_dir.exists():
        print(f"  ⚠ No poe.ninja economy data found for {game}")
        return

    # Find all league directories
    league_dirs = [d for d in economy_dir.iterdir() if d.is_dir()]

    if verbose:
        print(f"\n  Found {len(league_dirs)} leagues for {game}")

    for league_dir in league_dirs:
        currency_file = league_dir / "currency.json"

        if not currency_file.exists():
            if verbose:
                print(f"    ⚠ {league_dir.name}: No currency.json")
            continue

        result.files_processed += 1

        with open(currency_file) as f:
            data = json.load(f)

        if verbose:
            items_count = len(data.get("core", {}).get("items", []))
            print(f"    ✓ {league_dir.name}: {items_count} currencies")

        parse_poeninja_currency(data, game, league_dir.name, result)


def print_summary(result: ValidationResult):
    """Print validation summary."""
    print("\n" + "=" * 80)
    print("CURRENCY VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\nFiles processed: {result.files_processed}")
    print(f"Total currencies: {len(result.results)}")
    print(f"Unique currency names: {len(result.unique_currencies)}")

    if result.results:
        print(
            f"\n✓ Successful: {len(result.successes)}/{len(result.results)} "
            f"({result.success_rate:.1f}%)"
        )
        print(f"✗ Failed: {len(result.failures)}/{len(result.results)}")

        # Breakdown by game
        by_game = defaultdict(lambda: {"success": 0, "failed": 0})
        for status, game, *_ in result.results:
            if status == "SUCCESS":
                by_game[game]["success"] += 1
            else:
                by_game[game]["failed"] += 1

        print("\nBreakdown by game:")
        for game in sorted(by_game.keys()):
            stats = by_game[game]
            total = stats["success"] + stats["failed"]
            rate = (stats["success"] / total * 100) if total > 0 else 0
            print(f"  {game}: {stats['success']}/{total} ({rate:.1f}%)")

        # Show failures if any
        if result.failures:
            print(f"\n⚠ FAILURES ({len(result.failures)}):")
            for status, game, league, currency_name, error in result.failures[:10]:
                print(f"  [{game}/{league}] {currency_name}")
                print(f"    → {error}")

        # Sample currencies
        print("\n✓ Sample currencies (first 20):")
        for currency in sorted(result.unique_currencies)[:20]:
            print(f"  - {currency}")

        # Show PoE1 vs PoE2 differences
        poe1_currencies = {r[3] for r in result.results if r[0] == "SUCCESS" and r[1] == "poe1"}
        poe2_currencies = {r[3] for r in result.results if r[0] == "SUCCESS" and r[1] == "poe2"}

        print("\n📊 Currency Counts:")
        print(f"  PoE1: {len(poe1_currencies)} unique currencies")
        print(f"  PoE2: {len(poe2_currencies)} unique currencies")

        # Show game-specific currencies
        poe1_only = poe1_currencies - poe2_currencies
        poe2_only = poe2_currencies - poe1_currencies
        shared = poe1_currencies & poe2_currencies

        print(f"  Shared: {len(shared)} currencies")
        if poe1_only:
            print(f"  PoE1-only: {len(poe1_only)} (e.g., {list(poe1_only)[:3]})")
        if poe2_only:
            print(f"  PoE2-only: {len(poe2_only)} (e.g., {list(poe2_only)[:3]})")

    else:
        print("\n⚠ No currencies found to validate")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Currency model design against sample data"
    )
    parser.add_argument(
        "--game",
        choices=["poe1", "poe2", "all"],
        default="all",
        help="Which game to validate (default: all)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed progress")

    args = parser.parse_args()

    print("=" * 80)
    print("CURRENCY DOMAIN MODEL VALIDATION")
    print("=" * 80)
    print(f"\nGame: {args.game}")
    print(f"Verbose: {args.verbose}")

    result = ValidationResult()

    # Determine which games to validate
    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        print(f"\n--- Validating {game.upper()} ---")
        validate_poeninja_currencies(game, result, args.verbose)

    # Print summary
    print_summary(result)

    # Exit with error code if any failures
    sys.exit(1 if result.failures else 0)


if __name__ == "__main__":
    main()
