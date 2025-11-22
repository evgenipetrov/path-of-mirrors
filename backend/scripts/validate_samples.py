#!/usr/bin/env python3
"""
Validate collected sample data from all upstream sources.

Checks:
- File existence and readability
- JSON validity
- Data structure completeness
- Sample counts and sizes
"""

import json
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


def validate_poeninja_samples(base_path: Path, game: str) -> dict[str, Any]:
    """Validate poe.ninja samples for a game."""
    game_path = base_path / game / "poeninja"
    results = {
        "game": game,
        "economy": {"status": "not_found", "leagues": {}, "total_files": 0},
        "builds": {"status": "not_found", "leagues": {}, "total_files": 0},
        "index_state": {"status": "not_found", "files": 0},
        "meta": {"status": "not_found"},
    }

    if not game_path.exists():
        log.warning("game_path_not_found", path=str(game_path))
        return results

    # Check economy data
    economy_path = game_path / "economy"
    if economy_path.exists():
        results["economy"]["status"] = "found"
        for league_dir in economy_path.iterdir():
            if league_dir.is_dir():
                files = list(league_dir.glob("*.json"))
                results["economy"]["leagues"][league_dir.name] = {
                    "files": len(files),
                    "total_size": sum(f.stat().st_size for f in files),
                    "categories": [f.stem for f in files],
                }
                results["economy"]["total_files"] += len(files)

    # Check build data
    builds_path = game_path / "builds"
    if builds_path.exists():
        results["builds"]["status"] = "found"
        for league_dir in builds_path.iterdir():
            if league_dir.is_dir():
                search_files = list(league_dir.glob("search_*.json"))
                char_files = list(league_dir.glob("character_*.json"))
                results["builds"]["leagues"][league_dir.name] = {
                    "search_files": len(search_files),
                    "character_files": len(char_files),
                }
                results["builds"]["total_files"] += len(search_files) + len(char_files)

    # Check index state
    index_path = game_path / "index_state"
    if index_path.exists():
        files = list(index_path.glob("*.json"))
        results["index_state"]["status"] = "found" if files else "empty"
        results["index_state"]["files"] = len(files)

    # Check metadata
    meta_path = game_path / "meta.json"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            results["meta"]["status"] = "valid"
            results["meta"]["samples_count"] = len(meta.get("samples", []))
            results["meta"]["data_types"] = meta.get("data_types", [])
            results["meta"]["collector_version"] = meta.get("collector_version")
        except json.JSONDecodeError as e:
            results["meta"]["status"] = "invalid_json"
            results["meta"]["error"] = str(e)
        except Exception as e:
            results["meta"]["status"] = "error"
            results["meta"]["error"] = str(e)

    return results


def validate_json_sample(file_path: Path) -> dict[str, Any]:
    """Validate a single JSON file."""
    result = {
        "path": str(file_path.relative_to(file_path.parents[4])),
        "size_bytes": file_path.stat().st_size,
        "valid_json": False,
        "has_data": False,
    }

    try:
        with open(file_path) as f:
            data = json.load(f)
        result["valid_json"] = True

        # Check if data is non-empty
        if isinstance(data, dict):
            result["has_data"] = bool(data.get("lines")) or len(data) > 0
            result["keys"] = list(data.keys())[:10]  # First 10 keys
            if "lines" in data:
                result["item_count"] = len(data["lines"])
        elif isinstance(data, list):
            result["has_data"] = len(data) > 0
            result["item_count"] = len(data)

    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result


def main() -> None:
    """Main validation entry point."""
    # Resolve path - samples are at project root, scripts are in backend/scripts
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent / "_samples" / "data"

    print("\n" + "=" * 80)
    print("SAMPLE DATA VALIDATION REPORT")
    print("=" * 80 + "\n")

    # Validate poe.ninja samples
    print("POE.NINJA SAMPLES")
    print("-" * 80)

    for game in ["poe1", "poe2"]:
        results = validate_poeninja_samples(base_path, game)

        print(f"\n{game.upper()}:")
        print("  Economy Data:")
        print(f"    Status: {results['economy']['status']}")
        if results["economy"]["status"] == "found":
            print(f"    Total Files: {results['economy']['total_files']}")
            for league, data in results["economy"]["leagues"].items():
                print(f"    League '{league}':")
                print(f"      - Files: {data['files']}")
                print(f"      - Size: {data['total_size']:,} bytes")
                print(f"      - Categories: {', '.join(data['categories'][:5])}...")

        print("\n  Build Data:")
        print(f"    Status: {results['builds']['status']}")
        if results["builds"]["status"] == "found":
            print(f"    Total Files: {results['builds']['total_files']}")
            for league, data in results["builds"]["leagues"].items():
                print(f"    League '{league}':")
                print(f"      - Search files: {data['search_files']}")
                print(f"      - Character files: {data['character_files']}")

        print("\n  Index State:")
        print(f"    Status: {results['index_state']['status']}")
        print(f"    Files: {results['index_state']['files']}")

        print("\n  Metadata:")
        print(f"    Status: {results['meta']['status']}")
        if results["meta"]["status"] == "valid":
            print(f"    Samples: {results['meta']['samples_count']}")
            print(f"    Data Types: {', '.join(results['meta']['data_types'])}")
            print(f"    Version: {results['meta']['collector_version']}")

    # Validate a few sample files for comprehensibility
    print("\n" + "=" * 80)
    print("SAMPLE FILE VALIDATION (Economy Data)")
    print("-" * 80 + "\n")

    sample_files = [
        base_path / "poe1/poeninja/economy/standard/currency.json",
        base_path / "poe1/poeninja/economy/standard/uniqueweapon.json",
        base_path / "poe1/poeninja/economy/standard/skillgem.json",
    ]

    for sample_path in sample_files:
        if sample_path.exists():
            result = validate_json_sample(sample_path)
            print(f"File: {result['path']}")
            print(f"  Size: {result['size_bytes']:,} bytes")
            print(f"  Valid JSON: {result['valid_json']}")
            print(f"  Has Data: {result['has_data']}")
            if "item_count" in result:
                print(f"  Item Count: {result['item_count']}")
            if "keys" in result:
                print(f"  Keys: {', '.join(result['keys'])}")
            if "error" in result:
                print(f"  ERROR: {result['error']}")
            print()

    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
