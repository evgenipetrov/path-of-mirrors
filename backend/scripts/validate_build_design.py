"""Validate Build domain model design against real data.

This script validates the Build entity can successfully represent builds from:
- Path of Building XML exports
- poe.ninja build snapshots

Usage:
    uv run python scripts/validate_build_design.py
    uv run python scripts/validate_build_design.py --source pob
    uv run python scripts/validate_build_design.py --game poe2
    uv run python scripts/validate_build_design.py --verbose
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLES_DIR = PROJECT_ROOT / "_samples"


@dataclass
class ValidationResult:
    """Track validation results across all sources."""

    total: int = 0
    success: int = 0
    failures: list[tuple[str, str, str, str]] = field(default_factory=list)
    by_source: dict[str, tuple[int, int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0]))
    classes: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ascendancies: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add_success(self, source: str, game: str, filename: str, char_class: str, ascendancy: str):
        """Record successful build parse."""
        self.total += 1
        self.success += 1
        self.by_source[f"{game}/{source}"][0] += 1
        self.by_source[f"{game}/{source}"][1] += 1
        self.classes[char_class] += 1
        if ascendancy:
            self.ascendancies[ascendancy] += 1

    def add_failure(self, source: str, game: str, filename: str, build_name: str, error: str):
        """Record failed build parse."""
        self.total += 1
        self.by_source[f"{game}/{source}"][1] += 1
        self.failures.append((source, game, filename, f"{build_name}: {error}"))

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("BUILD VALIDATION SUMMARY")
        print("=" * 80)
        print()
        print(f"Total build validations: {self.total}")
        print(f"Unique classes: {len(self.classes)}")
        print(f"Unique ascendancies: {len(self.ascendancies)}")
        print()
        if self.total > 0:
            print(f"✓ Successful: {self.success}/{self.total} ({self.success/self.total*100:.1f}%)")
            print(f"✗ Failed: {len(self.failures)}/{self.total}")
        else:
            print("⚠ No builds found to validate")
            print("  Expected sample data in:")
            print(f"    - {SAMPLES_DIR}/poe1/pob_exports/*.xml")
            print(f"    - {SAMPLES_DIR}/poe1/poeninja_builds/{{league}}/*.json")
            print(f"    - {SAMPLES_DIR}/poe2/pob_exports/*.xml")
            print(f"    - {SAMPLES_DIR}/poe2/poeninja_builds/{{league}}/*.json")
        print()
        print("Breakdown by source:")
        for source, (success, total) in sorted(self.by_source.items()):
            pct = success / total * 100 if total > 0 else 0
            print(f"  {source}: {success}/{total} ({pct:.1f}%)")

        print()
        print(f"Character classes (top 10):")
        for char_class, count in sorted(self.classes.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {char_class}: {count}")

        print()
        print(f"Ascendancies (top 10):")
        for ascendancy, count in sorted(self.ascendancies.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ascendancy}: {count}")

        if self.failures:
            print()
            print(f"⚠ FAILURES ({len(self.failures)}):")
            for source, game, filename, error_msg in self.failures[:20]:
                print(f"  [{game}/{source}] {error_msg}")
            if len(self.failures) > 20:
                print(f"  ... and {len(self.failures) - 20} more")

        print()
        return len(self.failures) == 0


def parse_pob_build(
    xml_path: Path, result: ValidationResult, source: str, game: str, verbose: bool
) -> None:
    """Parse a Path of Building XML export.

    Validates that we can extract all required Build fields from PoB XML.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extract build metadata
        build_elem = root.find("Build")
        if build_elem is None:
            raise ValueError("No Build element found")

        # Required fields
        name = build_elem.get("name") or build_elem.get("className") or "Unnamed Build"
        char_class = build_elem.get("className")
        ascend_class = build_elem.get("ascendClassName")
        level = build_elem.get("level")

        if not char_class:
            raise ValueError("Missing className")
        if not level:
            raise ValueError("Missing level")

        # Extract stats (optional)
        # PoB stores calculated stats in various places - just validate structure exists
        items_elem = root.find("Items")
        skills_elem = root.find("Skills")
        tree_elem = root.find("Tree")

        # Simulate Build entity creation
        build_dict = {
            "game": game,
            "name": name,
            "character_class": char_class,
            "ascendancy": ascend_class,
            "level": int(level),
            "league": None,  # Not in PoB XML
            "life": None,  # Would need to parse calcs
            "energy_shield": None,
            "mana": None,
            "armour": None,
            "evasion": None,
            "passive_tree": {"nodes": []},  # tree_elem has the data
            "items": {},  # items_elem has the data
            "skills": [],  # skills_elem has the data
            "source": "pob",
            "pob_code": None,  # Would extract from pastebin or generate
            "properties": {},
        }

        # Validate required fields
        if not all([build_dict["game"], build_dict["name"],
                   build_dict["character_class"], build_dict["level"]]):
            raise ValueError("Missing required Build fields")

        result.add_success(source, game, xml_path.name, char_class, ascend_class or "None")

        if verbose:
            print(f"    ✓ {name}: {char_class} ({ascend_class or 'No ascendancy'}) Level {level}")

    except Exception as e:
        result.add_failure(source, game, xml_path.name, xml_path.stem, str(e))
        if verbose:
            print(f"    ✗ {xml_path.name}: {e}")


def parse_poeninja_build(
    build_data: dict, result: ValidationResult, source: str, game: str,
    league: str, verbose: bool
) -> None:
    """Parse a poe.ninja build snapshot.

    poe.ninja builds come from ladder API with character data.
    """
    try:
        # poe.ninja structure varies, but typically has:
        # - name, level, class, experience, etc.

        name = build_data.get("name") or "Unnamed"
        char_class = build_data.get("class")
        level = build_data.get("level")

        if not char_class:
            raise ValueError("Missing class")
        if not level:
            raise ValueError("Missing level")

        # Extract stats if available
        life = build_data.get("life")
        energy_shield = build_data.get("energy_shield")

        # Items are usually in "items" array
        items_data = build_data.get("items", [])

        # Skills in "skills" array
        skills_data = build_data.get("skills", [])

        # Passive tree might be in "passives" or "tree"
        tree_data = build_data.get("passives") or build_data.get("tree")

        # Simulate Build entity creation
        build_dict = {
            "game": game,
            "name": name,
            "character_class": char_class,
            "ascendancy": None,  # May need to derive from passives
            "level": int(level),
            "league": league,
            "life": life,
            "energy_shield": energy_shield,
            "mana": None,
            "armour": None,
            "evasion": None,
            "passive_tree": tree_data or {},
            "items": {"equipment": items_data},
            "skills": skills_data,
            "source": "poeninja",
            "pob_code": None,  # Would need to generate from data
            "properties": {},
        }

        if not all([build_dict["game"], build_dict["name"],
                   build_dict["character_class"], build_dict["level"]]):
            raise ValueError("Missing required Build fields")

        result.add_success(source, game, f"{league}.json", char_class, "Unknown")

        if verbose:
            print(f"    ✓ {name}: {char_class} Level {level}")

    except Exception as e:
        build_name = build_data.get("name", "Unknown")
        result.add_failure(source, game, league, build_name, str(e))
        if verbose:
            print(f"    ✗ {build_name}: {e}")


def validate_pob_exports(game: str, result: ValidationResult, verbose: bool) -> None:
    """Validate Path of Building XML exports."""
    pob_dir = SAMPLES_DIR / game / "pob_exports"
    if not pob_dir.exists():
        if verbose:
            print(f"  No PoB exports directory for {game}")
        return

    xml_files = list(pob_dir.glob("*.xml"))
    if not xml_files:
        if verbose:
            print(f"  No PoB XML files for {game}")
        return

    print(f"  Found {len(xml_files)} PoB files for {game}")

    for xml_file in xml_files:
        parse_pob_build(xml_file, result, "pob_exports", game, verbose)


def validate_poeninja_builds(game: str, result: ValidationResult, verbose: bool) -> None:
    """Validate poe.ninja build snapshots."""
    poeninja_dir = SAMPLES_DIR / game / "poeninja_builds"
    if not poeninja_dir.exists():
        if verbose:
            print(f"  No poe.ninja builds directory for {game}")
        return

    # Look for league directories or JSON files
    league_dirs = [d for d in poeninja_dir.iterdir() if d.is_dir()]

    if not league_dirs:
        if verbose:
            print(f"  No league directories in poe.ninja builds for {game}")
        return

    print(f"  Found {len(league_dirs)} leagues for {game}")

    for league_dir in league_dirs:
        league_name = league_dir.name
        json_files = list(league_dir.glob("*.json"))

        if not json_files:
            continue

        # Assume builds are in a single builds.json or multiple character files
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Data could be single build or array of builds
                builds = data if isinstance(data, list) else [data]

                if verbose:
                    print(f"    {league_name}: {len(builds)} builds")

                for build in builds:
                    parse_poeninja_build(build, result, "poeninja_builds", game, league_name, verbose)

            except Exception as e:
                result.add_failure("poeninja_builds", game, league_name, json_file.name, str(e))
                if verbose:
                    print(f"    ✗ {json_file.name}: {e}")


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description="Validate Build domain model")
    parser.add_argument("--game", choices=["poe1", "poe2", "all"], default="all",
                       help="Game to validate (default: all)")
    parser.add_argument("--source", choices=["pob", "poeninja", "all"], default="all",
                       help="Source to validate (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed output")

    args = parser.parse_args()

    print("=" * 80)
    print("BUILD DOMAIN MODEL VALIDATION")
    print("=" * 80)
    print()
    print(f"Game: {args.game}")
    print(f"Source: {args.source}")
    print(f"Verbose: {args.verbose}")
    print()

    result = ValidationResult()

    games = ["poe1", "poe2"] if args.game == "all" else [args.game]

    for game in games:
        print(f"--- Validating {game.upper()} ---")
        print()

        if args.source in ["pob", "all"]:
            validate_pob_exports(game, result, args.verbose)

        if args.source in ["poeninja", "all"]:
            validate_poeninja_builds(game, result, args.verbose)

        print()

    success = result.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
