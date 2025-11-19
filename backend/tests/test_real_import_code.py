"""Test parsing real PoB import code from file."""
import os
import pytest
from src.contexts.upstream.services.pob_parser import parse_pob_code
from src.shared import Game


def test_parse_real_import_code_from_sample_file():
    """Test parsing a real PoB import code (URL-safe base64) exported from PoB."""
    # Get path to import string file - this is the REAL code from PoB
    # (uses URL-safe base64 encoding with - and _ characters)
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    repo_root = os.path.dirname(backend_dir)
    import_code_path = os.path.join(repo_root, "_samples/data/poe1/pob/import_string.txt")

    # Read the import code
    with open(import_code_path, 'r') as f:
        import_code = f.read().strip()

    print(f"\nImport code length: {len(import_code)} characters")
    print(f"First 80 chars: {import_code[:80]}")
    print(f"Last 80 chars: {import_code[-80:]}")

    # Parse it
    build = parse_pob_code(import_code, Game.POE1)

    print(f"\n✅ Successfully parsed!")
    print(f"Build name: {build.name}")
    print(f"Character: Level {build.level} {build.character_class}")
    print(f"Ascendancy: {build.ascendancy}")
    print(f"Items: {len(build.items) if build.items else 0}")

    # Verify it parsed correctly (this is a Necromancer build)
    assert build is not None
    assert build.character_class == "Witch"
    assert build.level == 79
    assert build.ascendancy == "Necromancer"
    assert build.game == Game.POE1
    assert build.items is not None
    assert len(build.items) >= 10  # Should have multiple items (weapons, armor, jewelry, flasks)

    # Verify we got the active ItemSet (id=2), not the first one (id=1)
    # The active set should have items like "Bones of Ullr" boots
    assert any("Ullr" in str(item.get("name", "")) for item in build.items.values())
