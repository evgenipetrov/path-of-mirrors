"""Service for managing canonical stat definitions.

This module provides the single source of truth for valid stat names,
categories, and default weights across both PoE1 and PoE2.
"""

# Import the canonical DEFAULT_STAT_WEIGHTS from analysis context
from src.contexts.analysis.services.ranking import DEFAULT_STAT_WEIGHTS
from src.contexts.builds.domain.schemas import StatDefinition
from src.shared import Game


def _get_stat_display_name(stat_key: str) -> str:
    """Convert stat key to human-readable display name.

    Args:
        stat_key: Stat key (e.g., 'fire_res', 'energy_shield')

    Returns:
        Display name (e.g., 'Fire Resistance', 'Energy Shield')
    """
    # Handle common patterns
    name_map = {
        "life": "Life",
        "energy_shield": "Energy Shield",
        "mana": "Mana",
        "armour": "Armour",
        "evasion": "Evasion",
        "block": "Block",
        "spell_block": "Spell Block",
        "spell_suppression": "Spell Suppression",
        "fire_res": "Fire Resistance",
        "cold_res": "Cold Resistance",
        "lightning_res": "Lightning Resistance",
        "chaos_res": "Chaos Resistance",
        "strength": "Strength",
        "dexterity": "Dexterity",
        "intelligence": "Intelligence",
        "phys_damage_avg": "Physical Damage (Avg)",
        "phys_damage_percent": "Physical Damage %",
        "crit_multi": "Critical Strike Multiplier",
        "crit_chance": "Critical Strike Chance",
        "dps": "Total DPS",
        "ehp": "Effective HP",
        "max_hit": "Max Hit",
        "movement_speed": "Movement Speed",
        "attack_speed": "Attack Speed",
        "cast_speed": "Cast Speed",
    }

    return name_map.get(stat_key, stat_key.replace("_", " ").title())


def _get_stat_category(stat_key: str) -> str:
    """Determine the category for a given stat.

    Args:
        stat_key: Stat key

    Returns:
        Category name
    """
    if stat_key in ("life", "energy_shield", "mana", "armour", "evasion",
                     "block", "spell_block", "spell_suppression", "ehp", "max_hit"):
        return "defense"
    if stat_key.endswith("_res"):
        return "resistance"
    if stat_key in ("strength", "dexterity", "intelligence"):
        return "attribute"
    if "damage" in stat_key or "crit" in stat_key or stat_key == "dps":
        return "damage"
    return "utility"


def get_stat_definitions(game: Game) -> list[StatDefinition]:
    """Get all canonical stat definitions for a game.

    Args:
        game: Game context (poe1 or poe2)

    Returns:
        List of stat definitions
    """
    # For now, both games use the same stat definitions
    # In the future, we can differentiate based on game if needed
    stats = []

    for stat_key, default_weight in DEFAULT_STAT_WEIGHTS.items():
        stats.append(
            StatDefinition(
                key=stat_key,
                display_name=_get_stat_display_name(stat_key),
                category=_get_stat_category(stat_key),
                default_weight=default_weight,
            )
        )

    # Sort by category, then by key for consistent ordering
    stats.sort(key=lambda s: (s.category, s.key))

    return stats
