"""Tests for PoB Parser service.

Tests cover:
- Basic XML parsing (character class, level, ascendancy)
- PoB import code decoding (base64 + zlib)
- Real PoB file parsing
- Error handling (invalid XML, missing fields)
- Upstream data storage
"""

import pytest

from src.contexts.upstream.services.pob_parser import (
    parse_pob_xml,
    parse_pob_code,
    extract_item_from_slot,
)
from src.shared import Game


class TestBasicXMLParsing:
    """Test parsing PoB XML into Build objects."""

    def test_parse_minimal_pob_xml(self):
        """Test parsing minimal valid PoB XML."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch" level="90"/>
        </PathOfBuilding>
        """

        build = parse_pob_xml(xml, Game.POE1)

        assert build.game == Game.POE1
        assert build.character_class == "Witch"
        assert build.level == 90
        assert build.name == "Unnamed Build"  # Default name
        assert build.ascendancy is None
        assert build.source == "pob"

    def test_parse_pob_xml_with_ascendancy(self):
        """Test parsing PoB XML with ascendancy class."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Marauder" ascendClassName="Juggernaut" level="95" buildName="RF Jugg"/>
        </PathOfBuilding>
        """

        build = parse_pob_xml(xml, Game.POE1)

        assert build.character_class == "Marauder"
        assert build.ascendancy == "Juggernaut"
        assert build.level == 95
        assert build.name == "RF Jugg"

    def test_parse_pob_xml_stores_upstream_data(self):
        """Test that raw XML is stored in upstream_data."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch" level="90" buildName="Test"/>
        </PathOfBuilding>
        """

        build = parse_pob_xml(xml, Game.POE1)

        assert build.upstream_data is not None
        assert build.upstream_data["_tag"] == "PathOfBuilding"
        assert "_children" in build.upstream_data

    def test_parse_pob_xml_poe2(self):
        """Test parsing PoB XML for PoE2."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Monk" level="85"/>
        </PathOfBuilding>
        """

        build = parse_pob_xml(xml, Game.POE2)

        assert build.game == Game.POE2
        assert build.character_class == "Monk"


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_invalid_xml(self):
        """Test error handling for malformed XML."""
        invalid_xml = "this is not xml"

        with pytest.raises(ValueError, match="Invalid PoB XML"):
            parse_pob_xml(invalid_xml, Game.POE1)

    def test_missing_build_element(self):
        """Test error when <Build> element is missing."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <SomeOtherElement/>
        </PathOfBuilding>
        """

        with pytest.raises(ValueError, match="missing <Build> element"):
            parse_pob_xml(xml, Game.POE1)

    def test_missing_class_name(self):
        """Test error when className attribute is missing."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build level="90"/>
        </PathOfBuilding>
        """

        with pytest.raises(ValueError, match="missing className"):
            parse_pob_xml(xml, Game.POE1)

    def test_missing_level(self):
        """Test error when level attribute is missing."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch"/>
        </PathOfBuilding>
        """

        with pytest.raises(ValueError, match="missing level"):
            parse_pob_xml(xml, Game.POE1)

    def test_invalid_level(self):
        """Test error when level is not a number."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch" level="not-a-number"/>
        </PathOfBuilding>
        """

        with pytest.raises(ValueError, match="Invalid level value"):
            parse_pob_xml(xml, Game.POE1)


class TestRealPoBFiles:
    """Test parsing real PoB sample files."""

    def test_parse_sample_poe1_build(self):
        """Test parsing a real PoE1 sample build."""
        # Read sample file (relative to repo root)
        # __file__ is tests/contexts/upstream/services/test_pob_parser.py
        # Go up 5 levels: test_pob_parser.py -> services -> upstream -> contexts -> tests -> backend
        # Then up one more to repo root
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Sample build PoE 1.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        # Verify basic fields (based on file inspection)
        assert build.character_class == "Duelist"
        assert build.ascendancy == "Champion"
        assert build.level == 100
        assert build.game == Game.POE1
        assert build.source == "pob"
        assert build.upstream_data is not None

    def test_parse_necromancer_build(self):
        """Test parsing Raise Spectre Necromancer build."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Level 92 Raise Spectre Necromancer.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        assert build.character_class == "Witch"
        # Check if it's a necromancer (may or may not have ascendancy set)
        assert build.level == 92
        assert "Necromancer" in str(build.name) or build.ascendancy == "Necromancer"


class TestItemExtraction:
    """Test extracting items from equipment slots."""

    def test_parse_sample_build_with_items(self):
        """Test that items are extracted from sample build."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Sample build PoE 1.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        # Build should have items
        assert build.items is not None
        assert isinstance(build.items, dict)
        assert len(build.items) > 0

    def test_extract_weapon_slot(self):
        """Test extracting weapon from Weapon 1 slot."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Sample build PoE 1.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        # Extract weapon from slot
        weapon = extract_item_from_slot(build, "Weapon 1")

        assert weapon is not None
        assert "name" in weapon
        assert "base_type" in weapon
        assert "rarity" in weapon

    def test_parsed_item_has_mods(self):
        """Test that parsed items contain mods."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Sample build PoE 1.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        # Get first item from any slot
        if build.items:
            first_item = next(iter(build.items.values()))

            # Should have mods arrays
            assert "explicit_mods" in first_item
            assert "implicit_mods" in first_item
            assert isinstance(first_item["explicit_mods"], list)
            assert isinstance(first_item["implicit_mods"], list)

    def test_item_has_properties(self):
        """Test that items have properties like item level, quality, etc."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        repo_root = os.path.dirname(backend_dir)
        sample_path = os.path.join(repo_root, "_samples/data/poe1/pob/Sample build PoE 1.xml")

        with open(sample_path) as f:
            xml_content = f.read()

        build = parse_pob_xml(xml_content, Game.POE1)

        # Get first item
        if build.items:
            first_item = next(iter(build.items.values()))

            # Should have properties dict
            assert "properties" in first_item
            assert isinstance(first_item["properties"], dict)


class TestPoBCodeDecoding:
    """Test decoding PoB import codes (base64 + zlib)."""

    def test_parse_pob_code_basic(self):
        """Test parsing a valid PoB import code."""
        # Create a minimal valid PoB XML
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch" level="90"/>
        </PathOfBuilding>
        """

        # Encode it as PoB import code (zlib compress + base64 encode)
        import base64
        import zlib
        compressed = zlib.compress(xml.encode('utf-8'))
        import_code = base64.b64encode(compressed).decode('ascii')

        # Parse the code
        build = parse_pob_code(import_code, Game.POE1)

        assert build.character_class == "Witch"
        assert build.level == 90
        assert build.game == Game.POE1

    def test_parse_pob_code_with_whitespace(self):
        """Test that import codes with whitespace are cleaned properly."""
        # Create a minimal valid PoB XML
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Marauder" level="95"/>
        </PathOfBuilding>
        """

        # Encode it as PoB import code
        import base64
        import zlib
        compressed = zlib.compress(xml.encode('utf-8'))
        import_code = base64.b64encode(compressed).decode('ascii')

        # Add various whitespace (spaces, tabs, newlines)
        import_code_with_whitespace = f"  {import_code[:20]}\n{import_code[20:40]}\t{import_code[40:]}  "

        # Should still parse correctly after whitespace removal
        build = parse_pob_code(import_code_with_whitespace, Game.POE1)

        assert build.character_class == "Marauder"
        assert build.level == 95

    def test_parse_pob_code_empty_after_cleanup(self):
        """Test error when code is empty after removing whitespace."""
        with pytest.raises(ValueError, match="empty after removing whitespace"):
            parse_pob_code("   \n\t   ", Game.POE1)

    def test_parse_pob_code_invalid_characters(self):
        """Test error when code contains non-base64 characters."""
        invalid_code = "eNqVW2!@#$%^&*()"  # Invalid base64 characters

        with pytest.raises(ValueError, match="invalid characters for base64"):
            parse_pob_code(invalid_code, Game.POE1)

    def test_parse_pob_code_invalid_base64(self):
        """Test error when code is not valid base64."""
        # Valid base64 characters but invalid encoding (odd length, no padding)
        invalid_code = "abc"

        with pytest.raises(ValueError, match="Invalid base64"):
            parse_pob_code(invalid_code, Game.POE1)

    def test_parse_pob_code_invalid_zlib(self):
        """Test error when code doesn't contain valid zlib data."""
        # Valid base64 but not zlib compressed
        import base64
        not_compressed = base64.b64encode(b"not zlib data").decode('ascii')

        with pytest.raises(ValueError, match="too short"):
            parse_pob_code(not_compressed, Game.POE1)

    def test_parse_pob_code_url_safe_base64(self):
        """Test parsing codes that use URL-safe base64 encoding (- and _ instead of + and /)."""
        # Create a minimal valid PoB XML
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Ranger" level="88"/>
        </PathOfBuilding>
        """

        # Encode it as URL-safe PoB import code
        import base64
        import zlib
        compressed = zlib.compress(xml.encode('utf-8'))
        import_code = base64.urlsafe_b64encode(compressed).decode('ascii')

        # Should parse correctly with URL-safe base64
        build = parse_pob_code(import_code, Game.POE1)

        assert build.character_class == "Ranger"
        assert build.level == 88
