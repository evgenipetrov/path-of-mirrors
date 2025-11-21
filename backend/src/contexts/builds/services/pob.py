"""Path of Building (PoB) parser service.

This service parses Path of Building XML files and import codes into Build domain objects.

PoB Format:
    - XML-based structure with nested elements
    - Can be provided as raw XML or base64+zlib compressed "import code"
    - Contains build data: character class, passive tree, items, skills, config

Key Functions:
    - parse_pob_xml: Parse XML string into Build object
    - parse_pob_code: Decode and parse PoB import code
    - extract_item_from_slot: Get item from specific equipment slot

Example PoB Import Code:
    eNqVW2uT2zYS_StTqUrtnJpShwxyM...
    (This is base64(zlib.compress(xml_string)))
"""

import base64
import xml.etree.ElementTree as ET
import zlib
from typing import Any, cast

import structlog

from src.contexts.core.domain import Build
from src.shared import Game

logger = structlog.get_logger(__name__)


def parse_pob_xml(xml_content: str, game: Game) -> Build:
    """Parse PoB XML string into Build object.

    Args:
        xml_content: Raw XML string from PoB file
        game: Game context (POE1 or POE2)

    Returns:
        Build domain object with parsed data

    Raises:
        ValueError: If XML is malformed or missing required fields
        ET.ParseError: If XML cannot be parsed

    Example:
        >>> with open("build.xml") as f:
        ...     xml_content = f.read()
        >>> build = parse_pob_xml(xml_content, Game.POE1)
        >>> print(build.name, build.character_class, build.level)
    """
    try:
        tree = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid PoB XML: {e}")

    # Extract Build element (contains character info)
    build_elem = tree.find("Build")
    if build_elem is None:
        raise ValueError("PoB XML missing <Build> element")

    # Required fields
    character_class = build_elem.get("className")
    level_str = build_elem.get("level")

    if not character_class:
        raise ValueError("PoB XML missing className attribute")
    if not level_str:
        raise ValueError("PoB XML missing level attribute")

    try:
        level = int(level_str)
    except ValueError:
        raise ValueError(f"Invalid level value: {level_str}")

    # Optional fields
    ascendancy = build_elem.get("ascendClassName") or None
    build_name = build_elem.get("buildName") or "Unnamed Build"

    # Extract items from ItemSet
    items = extract_items(tree)

    # TODO: Extract passive tree
    passive_tree = None

    # TODO: Extract skills
    skills = None

    # Store raw XML as upstream_data for fidelity
    # Convert ET back to dict representation for JSONB storage
    upstream_data = _xml_to_dict(tree)

    return Build(
        game=game,
        name=build_name,
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        source="pob",
        items=items,
        passive_tree=passive_tree,
        skills=skills,
        upstream_data=upstream_data,
    )


def decode_pob_code_to_xml(import_code: str) -> str:
    """Decode PoB import code (base64+zlib) into XML string."""
    cleaned_code = "".join(import_code.split())

    if not cleaned_code:
        raise ValueError("PoB import code is empty after removing whitespace")

    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=-_"
    if not all(c in valid_chars for c in cleaned_code):
        invalid_chars = {c for c in cleaned_code if c not in valid_chars}
        raise ValueError(
            f"PoB import code contains invalid characters for base64 encoding: {invalid_chars}"
        )

    try:
        if "-" in cleaned_code or "_" in cleaned_code:
            compressed = base64.urlsafe_b64decode(cleaned_code)
        else:
            compressed = base64.b64decode(cleaned_code)
    except Exception as e:
        raise ValueError(f"Invalid base64 in PoB import code: {e}")

    try:
        xml_bytes = zlib.decompress(compressed)
        return xml_bytes.decode("utf-8")
    except zlib.error as e:
        error_msg = f"Failed to decompress PoB code: {e}"
        if len(cleaned_code) < 1000:
            error_msg = (
                "PoB import code is too short "
                f"({len(cleaned_code)} chars). Typical codes are 10,000+."
            )
        elif len(cleaned_code) < 5000:
            error_msg = (
                "PoB import code may be incomplete "
                f"({len(cleaned_code)} chars). Typical codes are 10,000+."
            )
        elif "invalid" in str(e).lower() or "incorrect" in str(e).lower():
            error_msg = (
                "PoB import code appears corrupted or incomplete "
                f"({len(cleaned_code)} chars). Try copying again from PoB."
            )
        raise ValueError(error_msg)
    except UnicodeDecodeError as e:
        raise ValueError(f"PoB import code decompressed to invalid UTF-8: {e}")
    except Exception as e:
        raise ValueError(f"Failed to decompress PoB import code: {e}")


def parse_pob_code(import_code: str, game: Game) -> Build:
    """Decode and parse PoB import code."""
    xml_content = decode_pob_code_to_xml(import_code)
    return parse_pob_xml(xml_content, game)


def extract_item_from_slot(build: Build, slot: str) -> dict | None:
    """Get current item from specific equipment slot.

    Args:
        build: Build object with items
        slot: Equipment slot name (e.g., "Weapon 1", "Amulet", "Ring 1")

    Returns:
        Item data dict or None if slot is empty

    Example:
        >>> build = parse_pob_code(code, Game.POE1)
        >>> amulet = extract_item_from_slot(build, "Amulet")
        >>> print(amulet["name"])
    """
    if build.items is None:
        return None

    return cast(dict[str, Any] | None, build.items.get(slot))


def parse_item_text(item_text: str) -> dict[str, Any]:
    """Parse PoB item text format into structured dict.

    PoB stores items as line-based text format:
        Rarity: UNIQUE
        Item Name
        Base Type
        Property: Value
        ...

    Args:
        item_text: Text content from <Item> element

    Returns:
        Dict with parsed item data

    Example:
        >>> text = '''Rarity: UNIQUE
        ... Foulborn Matua Tupuna
        ... Tarnished Spirit Shield
        ... Energy Shield: 33'''
        >>> item = parse_item_text(text)
        >>> print(item["name"], item["base_type"], item["rarity"])
    """
    lines = [line.strip() for line in item_text.strip().split("\n") if line.strip()]

    if not lines:
        return {}

    item_data: dict[str, Any] = {
        "explicit_mods": [],
        "implicit_mods": [],
        "properties": {},
    }

    # Parse rarity (first line)
    if lines[0].startswith("Rarity:"):
        item_data["rarity"] = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]

    # For unique/rare items: next line is name, then base type
    # For normal/magic items: only base type
    if item_data.get("rarity") in ["UNIQUE", "RARE"]:
        if len(lines) >= 2:
            item_data["name"] = lines[0]
            item_data["base_type"] = lines[1]
            lines = lines[2:]
    elif lines:
        item_data["name"] = None
        item_data["base_type"] = lines[0]
        lines = lines[1:]

    # Parse remaining lines as properties and mods
    in_implicits = False
    implicit_count = 0

    for line in lines:
        # Check for "Implicits: N" marker
        if line.startswith("Implicits:"):
            in_implicits = True
            implicit_count = int(line.split(":", 1)[1].strip())
            continue

        # Check for "Corrupted" marker
        if line == "Corrupted":
            item_data["corrupted"] = True
            continue

        # Parse key: value properties
        if ": " in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Known properties
            if key in ["Energy Shield", "Armour", "Evasion", "Quality", "Item Level", "LevelReq"]:
                # Store as property
                item_data["properties"][key] = value
            elif key in ["Sockets"]:
                item_data["sockets"] = value
            elif key == "Unique ID":
                item_data["unique_id"] = value
            else:
                # Unknown key:value, might be a property
                item_data["properties"][key] = value
        else:
            # Lines without colons are mods
            if in_implicits and implicit_count > 0:
                item_data["implicit_mods"].append(line)
                implicit_count -= 1
                if implicit_count == 0:
                    in_implicits = False
            else:
                # Explicit mod
                item_data["explicit_mods"].append(line)

    return item_data


def extract_items(tree: ET.Element) -> dict[str, dict]:
    """Extract items from PoB XML ItemSet.

    Args:
        tree: Root XML element (PathOfBuilding)

    Returns:
        Dict mapping slot names to item data dicts

    Example:
        >>> items = extract_items(tree)
        >>> print(items["Weapon 1"]["name"])
    """
    items_by_id: dict[str, dict] = {}
    slot_mapping: dict[str, dict] = {}

    # Find <Items> element and parse all <Item> children
    items_elem = tree.find("Items")
    if items_elem is None:
        return slot_mapping

    # Parse all items
    for item_elem in items_elem.findall("Item"):
        item_id = item_elem.get("id")
        item_text = item_elem.text or ""

        if item_id and item_text.strip():
            items_by_id[item_id] = parse_item_text(item_text)

    # Find the active ItemSet (default to '1' if not specified)
    active_item_set_id = items_elem.get("activeItemSet", "1")

    # Find <ItemSet> with the active ID
    item_set = tree.find(f".//ItemSet[@id='{active_item_set_id}']")
    if item_set is not None:
        for slot_elem in item_set.findall("Slot"):
            slot_name = slot_elem.get("name", "")
            item_id = slot_elem.get("itemId", "0")

            # Skip empty slots and non-equipment slots
            if item_id == "0":
                continue
            if "Abyssal" in slot_name or "Swap" in slot_name:
                continue  # Skip jewel sockets and weapon swap for MVP

            # Map slot to item
            if item_id in items_by_id:
                slot_mapping[slot_name] = items_by_id[item_id]

    return slot_mapping


def _xml_to_dict(element: ET.Element) -> dict[str, Any]:
    """Convert XML Element to dict representation for JSONB storage.

    Args:
        element: ET.Element to convert

    Returns:
        Dict representation of XML element
    """
    result: dict[str, Any] = {}

    # Add tag name
    result["_tag"] = element.tag

    # Add attributes
    if element.attrib:
        result["_attrib"] = dict(element.attrib)

    # Add text content
    if element.text and element.text.strip():
        result["_text"] = element.text.strip()

    # Add child elements
    children = list(element)
    if children:
        result["_children"] = [_xml_to_dict(child) for child in children]

    return result
