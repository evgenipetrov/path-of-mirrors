"""Build analysis service for calculating stat priorities and weights.

This module analyzes parsed builds to determine:
- Build archetype (life-based, ES-based, hybrid)
- Stat priorities based on current values
- Recommended stat weights for upgrade searches
- Gaps and weaknesses (e.g., uncapped resistances)

Phase 1 (MVP): Rule-based heuristics
Phase 2 (Future): PoB calculation engine integration for accurate DPS/EHP
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def calculate_build_weights(build_data: dict[str, Any]) -> dict[str, float]:
    """Calculate stat weights based on build characteristics.

    Uses heuristic rules to determine which stats are important for this build.

    Args:
        build_data: Parsed build data from session

    Returns:
        Dictionary of stat_key → weight (higher = more important)

    Example:
        >>> build = {"energy_shield": 5000, "life": 1000, ...}
        >>> weights = calculate_build_weights(build)
        >>> print(weights["energy_shield"], weights["life"])
        2.0 0.1  # ES build prioritizes ES
    """
    weights: dict[str, float] = {}

    # Extract key stats
    life = build_data.get("life", 0)
    energy_shield = build_data.get("energy_shield", 0)
    level = build_data.get("level", 1)

    logger.info(
        "Analyzing build",
        life=life,
        energy_shield=energy_shield,
        level=level,
    )

    # Determine build archetype
    if energy_shield and energy_shield > 2500:
        # ES-based build
        weights["energy_shield"] = 2.0
        weights["es_percent"] = 1.5
        weights["life"] = 0.1
        logger.info("Detected ES-based build archetype")
    elif life and life > 500:
        # Life-based build
        weights["life"] = 2.0
        weights["life_percent"] = 1.2
        weights["energy_shield"] = 0.1
        logger.info("Detected life-based build archetype")
    else:
        # Low-level or unknown - prioritize life by default
        weights["life"] = 1.5
        weights["energy_shield"] = 0.5
        logger.info("Default build archetype (low-level or unknown)")

    # Resistance priorities
    # TODO: Calculate actual total resists from items + tree
    # For MVP, use default weights
    if level < 70:
        # Leveling - resistances are critical
        weights["fire_res"] = 2.0
        weights["cold_res"] = 2.0
        weights["lightning_res"] = 2.0
        weights["chaos_res"] = 0.5
        logger.info("High resistance priority (leveling character)")
    else:
        # Endgame - assume capped, lower priority
        weights["fire_res"] = 0.8
        weights["cold_res"] = 0.8
        weights["lightning_res"] = 0.8
        weights["chaos_res"] = 0.6
        logger.info("Standard resistance priority (endgame)")

    # Attribute priorities (moderate)
    weights["strength"] = 0.4
    weights["dexterity"] = 0.4
    weights["intelligence"] = 0.4

    # Damage stats (generic weights for MVP)
    weights["phys_damage_avg"] = 0.7
    weights["phys_damage_percent"] = 0.6
    weights["crit_multi"] = 0.8
    weights["crit_chance"] = 0.6

    # Utility stats
    weights["movement_speed"] = 1.0  # Always valuable
    weights["attack_speed"] = 0.7
    weights["cast_speed"] = 0.7

    return weights


def analyze_build(build_data: dict[str, Any]) -> dict[str, Any]:
    """Perform comprehensive build analysis.

    Args:
        build_data: Parsed build data from session

    Returns:
        Analysis results with archetype, weights, and priorities

    Example:
        >>> analysis = analyze_build(build_data)
        >>> print(analysis["archetype"])
        "life_based"
        >>> print(analysis["suggested_weights"]["life"])
        2.0
    """
    # Determine archetype
    life = build_data.get("life", 0)
    energy_shield = build_data.get("energy_shield", 0)

    if energy_shield and energy_shield > 2500:
        archetype = "es_based"
    elif life and life > 500:
        archetype = "life_based"
    else:
        archetype = "unknown"

    # Calculate stat weights
    suggested_weights = calculate_build_weights(build_data)

    # Analyze item slots for upgrade priorities
    items = build_data.get("items", {})
    upgrade_priorities: dict[str, list[str]] = {}

    # For MVP, suggest basic priorities for each slot
    # In Phase 2, this would analyze actual item stats
    for slot in items.keys():
        if archetype == "es_based":
            upgrade_priorities[slot] = ["energy_shield", "es_percent"]
        else:
            upgrade_priorities[slot] = ["life", "fire_res", "cold_res"]

    logger.info(
        "Build analysis complete",
        archetype=archetype,
        num_weights=len(suggested_weights),
        num_slots=len(upgrade_priorities),
    )

    return {
        "archetype": archetype,
        "suggested_weights": suggested_weights,
        "upgrade_priorities": upgrade_priorities,
        "current_stats": {
            "life": life,
            "energy_shield": energy_shield,
            "level": build_data.get("level", 1),
        },
    }
