"""Stat extraction and normalization service.

This module normalizes stats from different sources (PoB items, Trade API items)
into a common format for comparison and ranking.

PoB Format:
    - Text strings: "+80 to maximum Life", "+45% to Fire Resistance"
    - Mixed formats: ranges, flat values, percentages

Trade API Format:
    - Stat IDs: "pseudo.pseudo_total_life", "explicit.stat_3372524247"
    - Values are numeric

Normalized Format:
    {
        "life": 80,
        "fire_res": 45,
        "cold_res": 32,
        "strength": 25,
        ...
    }

Phase 1 (MVP): Simple regex-based extraction for common stats
Phase 2: Full stat mapping with Trade API stat IDs
"""

import re
from typing import Any

# Common stat patterns for PoB mod text
# Format: (regex_pattern, normalized_key, value_extractor)
STAT_PATTERNS = [
    # Life
    (r"\+(\d+) to maximum Life", "life", lambda m: int(m.group(1))),
    (r"(\d+)% increased maximum Life", "life_percent", lambda m: int(m.group(1))),
    # Energy Shield
    (r"\+(\d+) to maximum Energy Shield", "energy_shield", lambda m: int(m.group(1))),
    (r"(\d+)% increased maximum Energy Shield", "es_percent", lambda m: int(m.group(1))),
    # Resistances
    (r"\+(\d+)% to Fire Resistance", "fire_res", lambda m: int(m.group(1))),
    (r"\+(\d+)% to Cold Resistance", "cold_res", lambda m: int(m.group(1))),
    (r"\+(\d+)% to Lightning Resistance", "lightning_res", lambda m: int(m.group(1))),
    (r"\+(\d+)% to Chaos Resistance", "chaos_res", lambda m: int(m.group(1))),
    (r"\+(\d+)% to all Elemental Resistances", "all_res", lambda m: int(m.group(1))),
    # Attributes
    (r"\+(\d+) to Strength", "strength", lambda m: int(m.group(1))),
    (r"\+(\d+) to Dexterity", "dexterity", lambda m: int(m.group(1))),
    (r"\+(\d+) to Intelligence", "intelligence", lambda m: int(m.group(1))),
    (r"\+(\d+) to all Attributes", "all_attributes", lambda m: int(m.group(1))),
    # Damage
    (
        r"Adds (\d+) to (\d+) Physical Damage",
        "phys_damage_avg",
        lambda m: (int(m.group(1)) + int(m.group(2))) / 2,
    ),
    (r"(\d+)% increased Physical Damage", "phys_damage_percent", lambda m: int(m.group(1))),
    # Attack/Cast Speed
    (r"(\d+)% increased Attack Speed", "attack_speed", lambda m: int(m.group(1))),
    (r"(\d+)% increased Cast Speed", "cast_speed", lambda m: int(m.group(1))),
    # Critical Strike
    (r"\+(\d+)% to Global Critical Strike Multiplier", "crit_multi", lambda m: int(m.group(1))),
    (r"(\d+)% increased Global Critical Strike Chance", "crit_chance", lambda m: int(m.group(1))),
    # Movement Speed
    (r"(\d+)% increased Movement Speed", "movement_speed", lambda m: int(m.group(1))),
]


def extract_stats_from_mods(mods: list[str]) -> dict[str, float]:
    """Extract normalized stats from PoB mod strings.

    Args:
        mods: List of mod text strings from PoB

    Returns:
        Dictionary of normalized stat keys → values

    Example:
        >>> mods = ["+80 to maximum Life", "+45% to Fire Resistance"]
        >>> stats = extract_stats_from_mods(mods)
        >>> print(stats)
        {"life": 80, "fire_res": 45}
    """
    stats: dict[str, float] = {}

    for mod in mods:
        for pattern, stat_key, extractor in STAT_PATTERNS:
            match = re.search(pattern, mod, re.IGNORECASE)
            if match:
                value = extractor(match)

                # If stat already exists, sum values (e.g., multiple life mods)
                if stat_key in stats:
                    stats[stat_key] += value
                else:
                    stats[stat_key] = value

                break  # Found a match, move to next mod

    return stats


def extract_stats_from_pob_item(item: dict[str, Any]) -> dict[str, float]:
    """Extract normalized stats from a PoB item dictionary.

    Args:
        item: PoB item dict with 'implicit_mods' and 'explicit_mods'

    Returns:
        Dictionary of normalized stats

    Example:
        >>> item = {
        ...     "implicit_mods": ["+25 to Dexterity"],
        ...     "explicit_mods": ["+80 to maximum Life", "+45% to Fire Resistance"]
        ... }
        >>> stats = extract_stats_from_pob_item(item)
        >>> print(stats)
        {"dexterity": 25, "life": 80, "fire_res": 45}
    """
    all_mods = []

    # Combine implicit and explicit mods
    if item.get("implicit_mods"):
        all_mods.extend(item["implicit_mods"])

    if item.get("explicit_mods"):
        all_mods.extend(item["explicit_mods"])

    return extract_stats_from_mods(all_mods)


def extract_stats_from_trade_item(trade_item: dict[str, Any]) -> dict[str, float]:
    """Extract normalized stats from a Trade API item.

    Phase 1 (MVP): Placeholder - returns empty dict
    Phase 2: Implement proper Trade API stat parsing

    Args:
        trade_item: Trade API item result

    Returns:
        Dictionary of normalized stats
    """
    # TODO: Implement Trade API stat extraction
    # For now, return empty dict (we'll focus on PoB items first)
    return {}


def calculate_total_resistances(stats: dict[str, float]) -> dict[str, float]:
    """Calculate total resistances including "all res" bonuses.

    Args:
        stats: Normalized stats dict

    Returns:
        Updated stats dict with calculated totals

    Example:
        >>> stats = {"fire_res": 30, "cold_res": 20, "all_res": 15}
        >>> updated = calculate_total_resistances(stats)
        >>> print(updated["fire_res"], updated["cold_res"])
        45 35
    """
    updated_stats = stats.copy()

    # Apply "all elemental resistances" bonus
    if "all_res" in updated_stats:
        all_res_bonus = updated_stats["all_res"]

        for res_key in ["fire_res", "cold_res", "lightning_res"]:
            if res_key in updated_stats:
                updated_stats[res_key] += all_res_bonus
            else:
                updated_stats[res_key] = all_res_bonus

    # Apply "all attributes" bonus
    if "all_attributes" in updated_stats:
        all_attr_bonus = updated_stats["all_attributes"]

        for attr_key in ["strength", "dexterity", "intelligence"]:
            if attr_key in updated_stats:
                updated_stats[attr_key] += all_attr_bonus
            else:
                updated_stats[attr_key] = all_attr_bonus

    return updated_stats


def get_item_summary(stats: dict[str, float]) -> str:
    """Generate a human-readable summary of item stats.

    Args:
        stats: Normalized stats dict

    Returns:
        Multi-line string summary

    Example:
        >>> stats = {"life": 80, "fire_res": 45, "strength": 25}
        >>> print(get_item_summary(stats))
        Life: +80
        Fire Resistance: +45%
        Strength: +25
    """
    lines = []

    # Define display names and formatting
    stat_display = {
        "life": ("Life", "+{}"),
        "energy_shield": ("Energy Shield", "+{}"),
        "fire_res": ("Fire Resistance", "+{}%"),
        "cold_res": ("Cold Resistance", "+{}%"),
        "lightning_res": ("Lightning Resistance", "+{}%"),
        "chaos_res": ("Chaos Resistance", "+{}%"),
        "strength": ("Strength", "+{}"),
        "dexterity": ("Dexterity", "+{}"),
        "intelligence": ("Intelligence", "+{}"),
        "movement_speed": ("Movement Speed", "+{}%"),
        "attack_speed": ("Attack Speed", "+{}%"),
        "cast_speed": ("Cast Speed", "+{}%"),
        "crit_multi": ("Critical Strike Multiplier", "+{}%"),
        "phys_damage_avg": ("Physical Damage", "~{} avg"),
    }

    for stat_key, value in sorted(stats.items()):
        if stat_key in stat_display:
            name, fmt = stat_display[stat_key]
            lines.append(f"{name}: {fmt.format(int(value))}")

    return "\n".join(lines) if lines else "No stats"
