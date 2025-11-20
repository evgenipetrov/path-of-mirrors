"""Quick script to inspect PoB item mod formats."""

import os
import sys

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from src.contexts.upstream.services.pob_parser import parse_pob_xml
from src.shared import Game

# Read sample PoE1 build
repo_root = os.path.dirname(backend_dir)
sample_path = os.path.join(repo_root, "samples", "pob", "poe1_sample.xml")

with open(sample_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

build = parse_pob_xml(xml_content, Game.POE1)

print("Build:", build.name)
print("Items found:", len(build.items) if build.items else 0)
print()

if build.items:
    for slot, item in list(build.items.items())[:3]:  # First 3 items
        print(f"=== {slot} ===")
        print(f"Base Type: {item.get('base_type')}")
        print(f"Rarity: {item.get('rarity')}")

        if item.get('implicit_mods'):
            print("\nImplicit Mods:")
            for mod in item['implicit_mods']:
                print(f"  - {mod}")

        if item.get('explicit_mods'):
            print("\nExplicit Mods:")
            for mod in item['explicit_mods'][:5]:  # First 5 mods
                print(f"  - {mod}")

        print()
