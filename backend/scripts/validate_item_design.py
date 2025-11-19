#!/usr/bin/env python3
"""
Validate Item domain model design against real sample data.

This script validates that the Item model can correctly represent items
from all upstream data sources (Trade API, poe.ninja, PoB) for both PoE1 and PoE2.

Usage:
    uv run python backend/scripts/validate_item_design.py
    uv run python backend/scripts/validate_item_design.py --source trade
    uv run python backend/scripts/validate_item_design.py --game poe2
    uv run python backend/scripts/validate_item_design.py --verbose

The validation logic demonstrates how to parse items from each upstream format.
The parsing functions will be reused when implementing adapters in Epic 1.4+.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


class ValidationResult:
    """Tracks validation results across all sources."""

    def __init__(self):
        self.results: list[tuple[str, str, str, str, str | None]] = []
        self.unique_items: set[str] = set()
        self.rarity_counts: dict[str, int] = defaultdict(int)
        self.files_processed = 0
        self.items_processed = 0

    def add_success(self, source: str, game: str, file: str, item_name: str):
        """Record successful parsing."""
        self.results.append(("SUCCESS", source, game, file, item_name, None))
        self.unique_items.add(item_name)

    def add_failure(self, source: str, game: str, file: str, item_name: str, error: str):
        """Record parsing failure."""
        self.results.append(("FAILED", source, game, file, item_name, error))

    def increment_rarity(self, rarity: str):
        """Increment count for rarity type."""
        self.rarity_counts[rarity] += 1

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


def parse_trade_api_item(
    item_data: dict, result: ValidationResult, source: str, game: str, filename: str
) -> None:
    """Parse items from Trade API format.

    Trade API format:
        {
            "item": {
                "name": "Soul Mantle",  # Empty for non-uniques
                "typeLine": "Spidersilk Robe",
                "baseType": "Spidersilk Robe",
                "rarity": "Unique",
                "ilvl": 84,
                "implicitMods": [...],
                "explicitMods": [...],
                "sockets": [...]
            }
        }

    This function demonstrates the adapter logic for Trade API → Item conversion.
    """
    item = item_data.get("item", {})
    if not item:
        return

    try:
        # Required fields
        name = item.get("name", "")
        type_line = item.get("typeLine")
        base_type = item.get("baseType", type_line)
        rarity = item.get("rarity")

        if not type_line or not rarity:
            raise ValueError("Missing required fields: typeLine or rarity")

        # Optional fields
        item_level = item.get("ilvl")
        item_class = item.get("itemClass")  # May not always be present

        # Modifiers (will be converted to Modifier.to_dict() format in real adapter)
        implicit_mods = item.get("implicitMods", [])
        explicit_mods = item.get("explicitMods", [])
        crafted_mods = item.get("craftedMods", [])
        enchant_mods = item.get("enchantMods", [])
        fractured_mods = item.get("fracturedMods", [])
        crucible_mods = item.get("crucibleMods", [])

        # Sockets
        sockets = item.get("sockets")

        # Properties (flexible JSONB)
        properties = item.get("properties", [])

        # Simulate Item entity creation
        item_dict = {
            "game": game,
            "name": name if name else None,
            "type_line": type_line,
            "base_type": base_type,
            "rarity": rarity,
            "item_level": item_level,
            "item_class": item_class,
            "implicit_mods": implicit_mods,
            "explicit_mods": explicit_mods,
            "crafted_mods": crafted_mods,
            "enchant_mods": enchant_mods,
            "fractured_mods": fractured_mods,
            "crucible_mods": crucible_mods,
            "scourge_mods": [],
            "sockets": sockets,
            "properties": properties,
        }

        # Validate required fields
        if not item_dict["type_line"] or not item_dict["rarity"]:
            raise ValueError("Missing required Item fields")

        result.add_success(source, game, filename, type_line)
        result.increment_rarity(rarity)

    except Exception as e:
        item_name = item.get("typeLine", "Unknown")
        result.add_failure(source, game, filename, item_name, str(e))


def parse_poeninja_item(
    item_data: dict, result: ValidationResult, source: str, game: str, filename: str
) -> None:
    """Parse items from poe.ninja build format.

    poe.ninja format:
        {
            "itemData": {
                "name": "Soul Mantle",
                "typeLine": "Spidersilk Robe",
                "baseType": "Spidersilk Robe",
                "rarity": "Unique",
                "ilvl": 84,
                "implicitMods": [...],
                "explicitMods": [...]
            }
        }

    This function demonstrates the adapter logic for poe.ninja → Item conversion.
    """
    item = item_data.get("itemData", {})
    if not item:
        return

    try:
        # Required fields
        name = item.get("name", "")
        type_line = item.get("typeLine")
        base_type = item.get("baseType", type_line)
        rarity = item.get("rarity")

        if not type_line or not rarity:
            raise ValueError("Missing required fields")

        # Optional fields
        item_level = item.get("ilvl")

        # Modifiers
        implicit_mods = item.get("implicitMods", [])
        explicit_mods = item.get("explicitMods", [])
        crafted_mods = item.get("craftedMods", [])
        enchant_mods = item.get("enchantMods", [])
        fractured_mods = item.get("fracturedMods", [])
        crucible_mods = item.get("crucibleMods", [])

        # Sockets
        sockets = item.get("sockets")

        # Simulate Item entity
        item_dict = {
            "game": game,
            "name": name if name else None,
            "type_line": type_line,
            "base_type": base_type,
            "rarity": rarity,
            "item_level": item_level,
            "implicit_mods": implicit_mods,
            "explicit_mods": explicit_mods,
            "crafted_mods": crafted_mods,
            "enchant_mods": enchant_mods,
            "fractured_mods": fractured_mods,
            "crucible_mods": crucible_mods,
            "sockets": sockets,
        }

        if not item_dict["type_line"] or not item_dict["rarity"]:
            raise ValueError("Missing required Item fields")

        result.add_success(source, game, filename, type_line)
        result.increment_rarity(rarity)

    except Exception as e:
        item_name = item.get("typeLine", "Unknown")
        result.add_failure(source, game, filename, item_name, str(e))


def parse_pob_item(
    item_element: ET.Element, result: ValidationResult, source: str, game: str, filename: str
) -> None:
    """Parse items from Path of Building XML format.

    PoB format:
        <Item>
        Rarity: UNIQUE
        Soul Mantle
        Spidersilk Robe
        ...
        </Item>

    This function demonstrates the adapter logic for PoB → Item conversion.
    """
    item_text = item_element.text if item_element.text else ""
    if not item_text.strip():
        return

    lines = item_text.strip().split("\n")
    if len(lines) < 2:
        return

    try:
        # Parse rarity from first line
        rarity_line = lines[0].strip()
        if not rarity_line.startswith("Rarity:"):
            return

        rarity = rarity_line.replace("Rarity:", "").strip()
        rarity = rarity.capitalize()  # "UNIQUE" -> "Unique"

        # Parse name and type_line
        # For uniques: name is on line 1, base on line 2
        # For rares: name is on line 1, base on line 2
        # For magic/normal: only base on line 1
        if rarity in ["Unique", "Rare"]:
            if len(lines) < 3:
                return
            name = lines[1].strip()
            type_line = lines[2].strip()
        else:
            if len(lines) < 2:
                return
            name = None
            type_line = lines[1].strip()

        base_type = type_line

        # Simulate Item entity
        item_dict = {
            "game": game,
            "name": name,
            "type_line": type_line,
            "base_type": base_type,
            "rarity": rarity,
        }

        if not item_dict["type_line"] or not item_dict["rarity"]:
            raise ValueError("Missing required Item fields")

        result.add_success(source, game, filename, type_line)
        result.increment_rarity(rarity)

    except Exception as e:
        result.add_failure(source, game, filename, "Unknown", str(e))


def validate_trade_api(game: str, result: ValidationResult, verbose: bool = False) -> None:
    """Validate Item against Trade API samples."""
    source = "trade_api"
    project_root = Path(__file__).parent.parent.parent
    trade_dir = project_root / f"_samples/data/{game}/trade"

    if not trade_dir.exists():
        print(f"  ⚠ No Trade API samples found for {game}")
        return

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

        if not data.get("items") or not data["items"].get("result"):
            if verbose:
                print(f"    ⚠ {sample_file.name}: No items")
            continue

        items = data["items"]["result"][:10]  # Process first 10
        result.items_processed += len(items)

        if verbose:
            print(f"    ✓ {sample_file.name}: {len(items)} items")

        for item_data in items:
            parse_trade_api_item(item_data, result, source, game, sample_file.name)


def validate_poeninja_builds(
    game: str, result: ValidationResult, verbose: bool = False
) -> None:
    """Validate Item against poe.ninja build samples."""
    source = "poeninja_builds"
    project_root = Path(__file__).parent.parent.parent
    builds_dir = project_root / f"_samples/data/{game}/poeninja/builds"

    if not builds_dir.exists():
        print(f"  ⚠ No poe.ninja builds found for {game}")
        return

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
                parse_poeninja_item(item, result, source, game, build_file.name)


def validate_pob_exports(game: str, result: ValidationResult, verbose: bool = False) -> None:
    """Validate Item against Path of Building exports."""
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
                parse_pob_item(item, result, source, game, pob_file.name)

        except Exception as e:
            if verbose:
                print(f"    ✗ {pob_file.name}: {e}")


def print_summary(result: ValidationResult):
    """Print validation summary."""
    print("\n" + "=" * 80)
    print("ITEM VALIDATION SUMMARY")
    print("=" * 80)

    print(f"\nFiles processed: {result.files_processed}")
    print(f"Items examined: {result.items_processed}")
    print(f"Total item validations: {len(result.results)}")
    print(f"Unique item types: {len(result.unique_items)}")

    if result.results:
        print(
            f"\n✓ Successful: {len(result.successes)}/{len(result.results)} "
            f"({result.success_rate:.1f}%)"
        )
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

        # Rarity distribution
        if result.rarity_counts:
            print("\nItem rarities:")
            for rarity, count in sorted(
                result.rarity_counts.items(), key=lambda x: -x[1]
            ):
                print(f"  {rarity}: {count}")

        # Show failures if any
        if result.failures:
            print(f"\n⚠ FAILURES ({len(result.failures)}):")
            unique_failures = list(
                set(
                    (source, game, text, error)
                    for _, source, game, _, text, error in result.failures
                )
            )
            for source, game, text, error in unique_failures[:10]:
                print(f"  [{game}/{source}] {text}")
                print(f"    → {error}")

        # Sample items
        print(f"\n✓ Sample items (first 15):")
        for item in sorted(list(result.unique_items))[:15]:
            print(f"  - {item}")
    else:
        print("\n⚠ No items found to validate")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Item model design against sample data"
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
    print("ITEM DOMAIN MODEL VALIDATION")
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
    print_summary(result)

    # Exit with error code if any failures
    sys.exit(1 if result.failures else 0)


if __name__ == "__main__":
    main()
