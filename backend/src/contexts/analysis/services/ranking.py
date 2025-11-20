"""Upgrade ranking service.

This module compares items and calculates improvement scores to rank potential upgrades.

Core Concept:
    - Compare current item vs. candidate item
    - Calculate improvement for each stat
    - Apply weights based on build priorities
    - Return ranked list of upgrades with scores

Scoring Algorithm (Phase 1 - Simple):
    score = Σ (stat_improvement * stat_weight)

Example:
    Current item: +60 life, +30% fire res
    Candidate: +80 life, +45% fire res
    Improvement: +20 life, +15% fire res
    Score: (20 * life_weight) + (15 * fire_res_weight)

Phase 2 Enhancements:
    - DPS calculations (requires PoB binary integration)
    - Defensive layer scoring (EHP calculations)
    - Build archetype detection (life vs ES vs hybrid)
"""

from dataclasses import dataclass
from typing import Any

# Updated import to point to catalog context
from src.contexts.catalog.services.stats import (
    calculate_total_resistances,
    extract_stats_from_pob_item,
)

# Default stat weights (higher = more important)
# These are sensible defaults but should be customizable per build
DEFAULT_STAT_WEIGHTS = {
    # Defenses (high priority for most builds)
    "life": 1.0,
    "energy_shield": 0.8,
    "fire_res": 0.6,
    "cold_res": 0.6,
    "lightning_res": 0.6,
    "chaos_res": 0.4,
    # Attributes (moderate priority)
    "strength": 0.3,
    "dexterity": 0.3,
    "intelligence": 0.3,
    # Damage (varies by build)
    "phys_damage_avg": 0.5,
    "phys_damage_percent": 0.4,
    "crit_multi": 0.5,
    "crit_chance": 0.4,
    # Utility
    "movement_speed": 0.7,
    "attack_speed": 0.5,
    "cast_speed": 0.5,
}


@dataclass
class UpgradeScore:
    """Result of comparing two items.

    Attributes:
        score: Overall improvement score (higher = better upgrade)
        improvements: Dict of stat improvements (positive = better, negative = worse)
        current_stats: Normalized stats from current item
        candidate_stats: Normalized stats from candidate item
        stat_weights: Weights used for scoring
        price_chaos: Price in chaos orbs (if available)
    """

    score: float
    improvements: dict[str, float]
    current_stats: dict[str, float]
    candidate_stats: dict[str, float]
    stat_weights: dict[str, float]
    price_chaos: float | None = None

    def __repr__(self) -> str:
        """String representation."""
        price_str = f", price={self.price_chaos}c" if self.price_chaos else ""
        return f"<UpgradeScore(score={self.score:.1f}{price_str})>"

    def get_summary(self) -> str:
        """Get human-readable summary of the upgrade.

        Returns:
            Multi-line string with improvement details
        """
        lines = [
            f"Upgrade Score: {self.score:.1f}",
        ]

        if self.price_chaos is not None:
            lines.append(f"Price: {self.price_chaos} chaos")

        if self.improvements:
            lines.append("\nImprovements:")
            for stat, change in sorted(
                self.improvements.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            ):
                if abs(change) < 0.1:  # Skip negligible changes
                    continue

                sign = "+" if change > 0 else ""
                stat_name = stat.replace("_", " ").title()
                lines.append(f"  {stat_name}: {sign}{change:.1f}")

        return "\n".join(lines)


def calculate_stat_improvements(
    current_stats: dict[str, float],
    candidate_stats: dict[str, float],
) -> dict[str, float]:
    """Calculate improvement for each stat.

    Args:
        current_stats: Normalized stats from current item
        candidate_stats: Normalized stats from candidate item

    Returns:
        Dict of stat improvements (positive = better, negative = worse)

    Example:
        >>> current = {"life": 60, "fire_res": 30}
        >>> candidate = {"life": 80, "fire_res": 45}
        >>> improvements = calculate_stat_improvements(current, candidate)
        >>> print(improvements)
        {"life": 20, "fire_res": 15}
    """
    improvements: dict[str, float] = {}

    # Get all unique stats from both items
    all_stats = set(current_stats.keys()) | set(candidate_stats.keys())

    for stat in all_stats:
        current_value = current_stats.get(stat, 0)
        candidate_value = candidate_stats.get(stat, 0)
        improvement = candidate_value - current_value

        if improvement != 0:
            improvements[stat] = improvement

    return improvements


def calculate_upgrade_score(
    current_stats: dict[str, float],
    candidate_stats: dict[str, float],
    stat_weights: dict[str, float] | None = None,
) -> float:
    """Calculate overall upgrade score.

    Score formula: Σ (stat_improvement * stat_weight)

    Args:
        current_stats: Normalized stats from current item
        candidate_stats: Normalized stats from candidate item
        stat_weights: Custom stat weights (uses DEFAULT_STAT_WEIGHTS if None)

    Returns:
        Overall improvement score (higher = better)

    Example:
        >>> current = {"life": 60, "fire_res": 30}
        >>> candidate = {"life": 80, "fire_res": 45}
        >>> score = calculate_upgrade_score(current, candidate)
        >>> print(score)  # (20 * 1.0) + (15 * 0.6) = 29.0
    """
    if stat_weights is None:
        stat_weights = DEFAULT_STAT_WEIGHTS

    improvements = calculate_stat_improvements(current_stats, candidate_stats)

    score = 0.0
    for stat, improvement in improvements.items():
        weight = stat_weights.get(stat, 0.0)
        score += improvement * weight

    return score


def compare_items(
    current_item: dict[str, Any],
    candidate_item: dict[str, Any],
    stat_weights: dict[str, float] | None = None,
    candidate_price: float | None = None,
) -> UpgradeScore:
    """Compare two items and return upgrade score.

    Args:
        current_item: Current PoB item dict
        candidate_item: Candidate PoB item dict (or Trade API item)
        stat_weights: Custom stat weights
        candidate_price: Price of candidate in chaos orbs

    Returns:
        UpgradeScore with comparison results

    Example:
        >>> current = {
        ...     "explicit_mods": ["+60 to maximum Life", "+30% to Fire Resistance"]
        ... }
        >>> candidate = {
        ...     "explicit_mods": ["+80 to maximum Life", "+45% to Fire Resistance"]
        ... }
        >>> result = compare_items(current, candidate)
        >>> print(result.score, result.improvements)
    """
    # Extract and normalize stats
    current_stats = extract_stats_from_pob_item(current_item)
    current_stats = calculate_total_resistances(current_stats)

    candidate_stats = extract_stats_from_pob_item(candidate_item)
    candidate_stats = calculate_total_resistances(candidate_stats)

    # Calculate improvements
    improvements = calculate_stat_improvements(current_stats, candidate_stats)

    # Calculate score
    if stat_weights is None:
        stat_weights = DEFAULT_STAT_WEIGHTS

    score = calculate_upgrade_score(current_stats, candidate_stats, stat_weights)

    return UpgradeScore(
        score=score,
        improvements=improvements,
        current_stats=current_stats,
        candidate_stats=candidate_stats,
        stat_weights=stat_weights,
        price_chaos=candidate_price,
    )


def rank_upgrades(
    current_item: dict[str, Any],
    candidates: list[dict[str, Any]],
    stat_weights: dict[str, float] | None = None,
    candidate_prices: list[float | None] | None = None,
) -> list[UpgradeScore]:
    """Rank multiple candidate items as potential upgrades.

    Args:
        current_item: Current PoB item dict
        candidates: List of candidate items
        stat_weights: Custom stat weights
        candidate_prices: Optional list of prices for each candidate

    Returns:
        List of UpgradeScores sorted by score (best first)

    Example:
        >>> current = {"explicit_mods": ["+60 to maximum Life"]}
        >>> candidates = [
        ...     {"explicit_mods": ["+80 to maximum Life"]},
        ...     {"explicit_mods": ["+100 to maximum Life"]},
        ... ]
        >>> results = rank_upgrades(current, candidates)
        >>> print(results[0].score > results[1].score)  # Best first
    """
    if candidate_prices is None:
        candidate_prices = [None] * len(candidates)

    results = []
    for candidate, price in zip(candidates, candidate_prices):
        result = compare_items(current_item, candidate, stat_weights, price)
        results.append(result)

    # Sort by score (highest first)
    results.sort(key=lambda x: x.score, reverse=True)

    return results


def calculate_value_score(upgrade_score: UpgradeScore) -> float | None:
    """Calculate value score (improvement per chaos spent).

    This helps identify "best bang for buck" upgrades.

    Args:
        upgrade_score: UpgradeScore with price information

    Returns:
        Value score (score / price) or None if no price

    Example:
        >>> score = UpgradeScore(
        ...     score=30.0,
        ...     improvements={},
        ...     current_stats={},
        ...     candidate_stats={},
        ...     stat_weights={},
        ...     price_chaos=10.0,
        ... )
        >>> value = calculate_value_score(score)
        >>> print(value)  # 3.0 (30 / 10)
    """
    if upgrade_score.price_chaos is None or upgrade_score.price_chaos <= 0:
        return None

    return upgrade_score.score / upgrade_score.price_chaos
