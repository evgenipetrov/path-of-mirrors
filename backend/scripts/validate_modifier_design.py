#!/usr/bin/env python3
"""
Validate Modifier value object design against real sample data.

This script validates that the Modifier design can correctly parse modifiers
from all upstream data sources (Trade API, poe.ninja, PoB) for both PoE1 and PoE2.

Usage:
    uv run python scripts/validate_modifier_design.py
    uv run python scripts/validate_modifier_design.py --source trade
    uv run python scripts/validate_modifier_design.py --game poe2
    uv run python scripts/validate_modifier_design.py --verbose

The validation logic in this script will be reused when implementing adapters
in Epic 1.4+. The parsing functions demonstrate how to extract modifiers from
each upstream format.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

# Import Modifier directly without triggering SQLAlchemy imports
# We only need the value object, not the entity models
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import just the Modifier module to avoid SQLAlchemy initialization
import importlib.util
spec = importlib.util.spec_from_file_location(
    "modifier",
    Path(__file__).parent.parent / "src" / "contexts" / "core" / "domain" / "modifier.py",
)
modifier_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modifier_module)

Modifier = modifier_module.Modifier
ModifierType = modifier_module.ModifierType


class ValidationResult:
    """Tracks validation results across all sources."""

    def __init__(self):
        self.results: list[tuple[str, str, str, str, str | None]] = []
        self.unique_mods: set[str] = set()
        self.mod_type_counts: dict[str, int] = defaultdict(int)
        self.files_processed = 0
        self.items_processed = 0

    def add_success(self, source: str, game: str, file: str, mod_text: str):
        """Record successful parsing."""
        self.results.append(("SUCCESS", source, game, file, mod_text, None))
        self.unique_mods.add(mod_text)

    def add_failure(self, source: str, game: str, file: str, mod_text: str, error: str):
        """Record parsing failure."""
        self.results.append(("FAILED", source, game, file, mod_text, error))

    def increment_mod_type(self, mod_type: str):
        """Increment count for modifier type."""
        self.mod_type_counts[mod_type] += 1

    @property
    def successes(self) -> list[tuple]:
        return [r for r in self.results if r[0] == "SUCCESS"]

    @property
    def failures(self) -> list[tuple]:
        return [r for r in self.results if r[0] == "FAILED"]

    @property
    def success_rate(self) -> float:
        total = len(self.results)
        return (len(self.successes) / total * 100) if total > 0 else 0


def parse_trade_api_modifiers(
    item: dict[str, Any], result: ValidationResult, source: str, game: str, filename: str
) -> None:
    """Parse modifiers from Trade API item format.

    Trade API format:
        item: {
            "implicitMods": ["mod text 1", "mod text 2"],
            "explicitMods": ["mod text 1"],
            "craftedMods": ["mod text 1"],
            "enchantMods": ["mod text 1"],
            "fracturedMods": ["mod text 1"],
            "crucibleMods": ["mod text 1"],  # PoE1 only
        }

    This function demonstrates the adapter logic for Trade API → Modifier conversion.
    """
    mod_keys = {
        "implicitMods": ModifierType.IMPLICIT,
        "explicitMods": ModifierType.EXPLICIT,
        "craftedMods": ModifierType.CRAFTED,
        "enchantMods": ModifierType.ENCHANT,
        "fracturedMods": ModifierType.FRACTURED,
        "crucibleMods": ModifierType.CRUCIBLE,
    }

    for key, mod_type in mod_keys.items():
        if key not in item or not item[key]:
            continue

        result.increment_mod_type(key)

        for mod_text in item[key]:
            try:
                # This is the core adapter logic: text → Modifier
                mod = Modifier.from_text(mod_type, mod_text)
                result.add_success(source, game, filename, mod_text)
            except Exception as e:
                result.add_failure(source, game, filename, mod_text, str(e))


def parse_poeninja_modifiers(
    item_data: dict[str, Any],
    result: ValidationResult,
    source: str,
    game: str,
    filename: str,
) -> None:
    """Parse modifiers from poe.ninja build item format.

    poe.ninja format:
        itemData: {
            "implicitMods": ["mod text 1"],
            "explicitMods": ["mod text 1"],
            "craftedMods": ["mod text 1"],
            "enchantMods": ["mod text 1"],
            "fracturedMods": ["mod text 1"],
            "crucibleMods": ["mod text 1"],  # PoE1 only
        }

    This function demonstrates the adapter logic for poe.ninja → Modifier conversion.
    """
    mod_keys = {
        "implicitMods": ModifierType.IMPLICIT,
        "explicitMods": ModifierType.EXPLICIT,
        "craftedMods": ModifierType.CRAFTED,
        "enchantMods": ModifierType.ENCHANT,
        "fracturedMods": ModifierType.FRACTURED,
        "crucibleMods": ModifierType.CRUCIBLE,
    }

    for key, mod_type in mod_keys.items():
        if key not in item_data or not item_data[key]:
            continue

        result.increment_mod_type(key)

        for mod_text in item_data[key]:
            try:
                mod = Modifier.from_text(mod_type, mod_text)
                result.add_success(source, game, filename, mod_text)
            except Exception as e:
                result.add_failure(source, game, filename, mod_text, str(e))


def parse_pob_modifiers(
    item_element: ET.Element,
    result: ValidationResult,
    source: str,
    game: str,
    filename: str,
) -> None:
    """Parse modifiers from Path of Building XML format.

    PoB format:
        <Item>
        Rarity: RARE
        Item text here
        mod text line 1
        mod text line 2
        </Item>

    This function demonstrates the adapter logic for PoB → Modifier conversion.
    """
    item_text = item_element.text if item_element.text else ""
    lines = item_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip header lines
        if line.startswith("Implicits:") or "Implicit" in line:
            continue

        # Check if line looks like a modifier (has numbers or keywords)
        if any(char.isdigit() for char in line) or any(
            keyword in line
            for keyword in [
                "increased",
                "to",
                "per",
                "Grants",
                "Cannot",
                "Adds",
                "reduced",
            ]
        ):
            # PoB doesn't distinguish mod types well, default to EXPLICIT
            mod_type = ModifierType.EXPLICIT
            result.increment_mod_type("pob_mods")

            try:
                mod = Modifier.from_text(mod_type, line)
                result.add_success(source, game, filename, line)
            except Exception as e:
                result.add_failure(source, game, filename, line, str(e))


def validate_trade_api(game: str, result: ValidationResult, verbose: bool = False) -> None:
    """Validate Modifier against Trade API samples."""
    source = "trade_api"
    # Find project root (go up from backend/scripts to project root)
    project_root = Path(__file__).parent.parent.parent
    trade_dir = project_root / f"_samples/data/{game}/trade"

    if not trade_dir.exists():
        print(f"  ⚠ No Trade API samples found for {game}")
        return

    # Find all Trade API sample files (exclude schemas)
    sample_files = [
        f
        for f in trade_dir.glob("**/*.json")
        if "schema" not in f.name and f.name not in ["meta.json", "schemas.json"]
    ]

    if verbose:
        print(f"\n  Found {len(sample_files)} Trade API files for {game}")

    for sample_file in sample_files:
        result.files_processed += 1

        with open(sample_file) as f:
            data = json.load(f)

        # Check if file has item data
        if not data.get("items") or not data["items"].get("result"):
            if verbose:
                print(f"    ⚠ {sample_file.name}: No items")
            continue

        items = data["items"]["result"][:10]  # Process first 10
        result.items_processed += len(items)

        if verbose:
            print(f"    ✓ {sample_file.name}: {len(items)} items")

        for item_data in items:
            item = item_data.get("item", {})
            parse_trade_api_modifiers(item, result, source, game, sample_file.name)


def validate_poeninja_builds(
    game: str, result: ValidationResult, verbose: bool = False
) -> None:
    """Validate Modifier against poe.ninja build samples."""
    source = "poeninja_builds"
    project_root = Path(__file__).parent.parent.parent
    builds_dir = project_root / f"_samples/data/{game}/poeninja/builds"

    if not builds_dir.exists():
        print(f"  ⚠ No poe.ninja builds found for {game}")
        return

    # Find all league directories
    league_dirs = [d for d in builds_dir.iterdir() if d.is_dir()]

    if verbose:
        print(f"\n  Found {len(league_dirs)} leagues for {game}")

    for league_dir in league_dirs:
        build_files = list(league_dir.glob("character_*.json"))[:15]  # Max 15 files

        if verbose:
            print(f"    {league_dir.name}: {len(build_files)} builds")

        for build_file in build_files:
            result.files_processed += 1

            with open(build_file) as f:
                data = json.load(f)

            if "items" not in data:
                continue

            items = data["items"]
            for item in items:
                if not item or "itemData" not in item:
                    continue

                result.items_processed += 1
                item_data = item["itemData"]
                parse_poeninja_modifiers(item_data, result, source, game, build_file.name)


def validate_pob_exports(game: str, result: ValidationResult, verbose: bool = False) -> None:
    """Validate Modifier against Path of Building exports."""
    source = "pob_exports"
    project_root = Path(__file__).parent.parent.parent
    pob_dir = project_root / f"_samples/data/{game}/pob"

    if not pob_dir.exists():
        print(f"  ⚠ No PoB exports found for {game}")
        return

    pob_files = list(pob_dir.glob("*.xml"))

    if verbose:
        print(f"\n  Found {len(pob_files)} PoB files for {game}")

    for pob_file in pob_files:
        result.files_processed += 1

        try:
            tree = ET.parse(pob_file)
            root = tree.getroot()

            items = root.findall(".//Item")
            result.items_processed += len(items)

            if verbose:
                print(f"    ✓ {pob_file.name}: {len(items)} items")

            for item in items:
                parse_pob_modifiers(item, result, source, game, pob_file.name)

        except Exception as e:
            if verbose:
                print(f"    ✗ {pob_file.name}: {e}")


def print_summary(result: ValidationResult, game_filter: str | None = None):
    """Print validation summary."""
    print("\n" + "=" * 80)
    print("MODIFIER VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\nFiles processed: {result.files_processed}")
    print(f"Items examined: {result.items_processed}")
    print(f"Total modifiers: {len(result.results)}")
    print(f"Unique modifier texts: {len(result.unique_mods)}")

    if result.results:
        print(f"\n✓ Successful: {len(result.successes)}/{len(result.results)} ({result.success_rate:.1f}%)")
        print(f"✗ Failed: {len(result.failures)}/{len(result.results)}")

        # Breakdown by source and game
        by_source_game = defaultdict(lambda: {"success": 0, "failed": 0})
        for status, source, game, *_ in result.results:
            key = f"{game}/{source}"
            if status == "SUCCESS":
                by_source_game[key]["success"] += 1
            else:
                by_source_game[key]["failed"] += 1

        print("\nBreakdown by source:")
        for key in sorted(by_source_game.keys()):
            stats = by_source_game[key]
            total = stats["success"] + stats["failed"]
            rate = (stats["success"] / total * 100) if total > 0 else 0
            print(f"  {key}: {stats['success']}/{total} ({rate:.1f}%)")

        # Modifier type distribution
        if result.mod_type_counts:
            print("\nModifier types:")
            for key, count in sorted(result.mod_type_counts.items(), key=lambda x: -x[1]):
                print(f"  {key}: {count}")

        # Show failures if any
        if result.failures:
            print(f"\n⚠ FAILURES ({len(result.failures)}):")
            unique_failures = list(
                set((source, game, text, error) for _, source, game, _, text, error in result.failures)
            )
            for source, game, text, error in unique_failures[:10]:
                print(f"  [{game}/{source}] {text}")
                print(f"    → {error}")

        # Sample successful modifiers
        print(f"\n✓ Sample modifiers (first 15):")
        for mod in sorted(list(result.unique_mods))[:15]:
            print(f"  - {mod}")
    else:
        print("\n⚠ No modifiers found to validate")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Modifier design against sample data"
    )
    parser.add_argument(
        "--game",
        choices=["poe1", "poe2", "all"],
        default="all",
        help="Which game to validate (default: all)",
    )
    parser.add_argument(
        "--source",
        choices=["trade", "poeninja", "pob", "all"],
        default="all",
        help="Which data source to validate (default: all)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed progress"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MODIFIER VALUE OBJECT VALIDATION")
    print("=" * 80)
    print(f"\nGame: {args.game}")
    print(f"Source: {args.source}")
    print(f"Verbose: {args.verbose}")

    result = ValidationResult()

    # Determine which games to validate
    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        print(f"\n--- Validating {game.upper()} ---")

        # Validate each source
        if args.source in ["trade", "all"]:
            validate_trade_api(game, result, args.verbose)

        if args.source in ["poeninja", "all"]:
            validate_poeninja_builds(game, result, args.verbose)

        if args.source in ["pob", "all"]:
            validate_pob_exports(game, result, args.verbose)

    # Print summary
    print_summary(result, args.game if args.game != "all" else None)

    # Exit with error code if any failures
    sys.exit(1 if result.failures else 0)


if __name__ == "__main__":
    main()
