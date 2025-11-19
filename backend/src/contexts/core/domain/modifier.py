"""Modifier domain value object.

Modifiers are the core mechanic of Path of Exile itemization.
They represent individual stat bonuses/penalties on items (affixes, implicits, etc.).

This is a value object (not an entity) - modifiers exist as properties of items,
not as independent database records.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ModifierType(str, Enum):
    """Types of modifiers that can appear on items.

    Different modifier types have different rules and behaviors:
    - IMPLICIT: Inherent to the item base type (e.g., "+2 Life per second" on Coral Amulet)
    - EXPLICIT: Random affixes (prefixes/suffixes) rolled on magic/rare items
    - CRAFTED: Player-added mods via crafting bench
    - ENCHANT: Lab enchantments or other special enchants
    - FRACTURED: Locked mods from fractured items
    - CRUCIBLE: Special mods from Crucible league (PoE1 only)
    - SCOURGE: Special mods from Scourge league (PoE1 only)
    - SYNTHESISED: Mods from Synthesis league (PoE1 only)
    """

    IMPLICIT = "implicit"
    EXPLICIT = "explicit"
    CRAFTED = "crafted"
    ENCHANT = "enchant"
    FRACTURED = "fractured"
    CRUCIBLE = "crucible"
    SCOURGE = "scourge"
    SYNTHESISED = "synthesised"

    def __str__(self) -> str:
        """Return string value."""
        return self.value


@dataclass(frozen=True)
class Modifier:
    """Represents a single modifier on an item.

    Modifiers are immutable value objects that represent stat bonuses/penalties.
    They can be stored as JSONB arrays on Item entities.

    Examples:
        - Implicit: Modifier(
            type=ModifierType.IMPLICIT,
            text="Regenerate 2.2 Life per second",
            values=[Decimal("2.2")]
          )

        - Explicit: Modifier(
            type=ModifierType.EXPLICIT,
            text="+21% to Lightning Resistance",
            values=[Decimal("21")]
          )

        - Crafted: Modifier(
            type=ModifierType.CRAFTED,
            text="+32 to maximum Life",
            values=[Decimal("32")]
          )

    Attributes:
        type: The modifier type (implicit, explicit, crafted, etc.)
        text: Human-readable text representation (e.g., "+42% to Fire Resistance")
        values: Numeric values extracted from the text (can be single or multiple)
        tier: Optional tier information (e.g., "T1", "T2") from RePoE data
    """

    type: ModifierType
    text: str
    values: tuple[Decimal, ...]  # Tuple for immutability
    tier: str | None = None

    def __post_init__(self) -> None:
        """Validate modifier data."""
        if not self.text:
            raise ValueError("Modifier text cannot be empty")

        if not self.values:
            raise ValueError("Modifier must have at least one value")

        # Validate tier format if provided
        if self.tier and not (self.tier.startswith("T") or self.tier == "Unique"):
            raise ValueError(f"Invalid tier format: {self.tier}")

    @property
    def value(self) -> Decimal:
        """Get the first (or only) value.

        Convenience property for modifiers with a single value.
        For multi-value mods, use .values instead.

        Returns:
            The first value in the values tuple.
        """
        return self.values[0]

    @property
    def has_range(self) -> bool:
        """Check if modifier has a value range (e.g., "Adds 4 to 6 Physical Damage").

        Returns:
            True if modifier has 2+ distinct values (min/max range).
        """
        return len(self.values) > 1 and len(set(self.values)) > 1

    @property
    def value_min(self) -> Decimal | None:
        """Get minimum value for ranged modifiers.

        Returns:
            Minimum value if has_range, else None.
        """
        return min(self.values) if self.has_range else None

    @property
    def value_max(self) -> Decimal | None:
        """Get maximum value for ranged modifiers.

        Returns:
            Maximum value if has_range, else None.
        """
        return max(self.values) if self.has_range else None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSONB storage.

        Returns:
            Dictionary representation suitable for database storage.
        """
        return {
            "type": self.type.value,
            "text": self.text,
            "values": [str(v) for v in self.values],  # Store as strings to preserve precision
            "tier": self.tier,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Modifier":
        """Create Modifier from dictionary (from JSONB).

        Args:
            data: Dictionary from database JSONB field.

        Returns:
            Modifier instance.

        Raises:
            ValueError: If data is invalid.
        """
        return cls(
            type=ModifierType(data["type"]),
            text=data["text"],
            values=tuple(Decimal(v) for v in data["values"]),
            tier=data.get("tier"),
        )

    @classmethod
    def from_text(cls, modifier_type: ModifierType, text: str) -> "Modifier":
        """Parse modifier from text string.

        Extracts numeric values from modifier text using simple pattern matching.
        This is a basic implementation - more sophisticated parsing will be needed
        for complex mods with multiple values or conditional text.

        Args:
            modifier_type: The type of modifier (implicit, explicit, etc.)
            text: The modifier text (e.g., "+42% to Fire Resistance")

        Returns:
            Modifier instance with extracted values.

        Examples:
            >>> Modifier.from_text(
            ...     ModifierType.EXPLICIT, "+21% to Lightning Resistance"
            ... )
            Modifier(type=ModifierType.EXPLICIT, ...)

            >>> Modifier.from_text(
            ...     ModifierType.EXPLICIT, "Adds 4 to 6 Physical Damage"
            ... )
            Modifier(type=ModifierType.EXPLICIT, ...)
        """
        import re

        # Extract all numbers (including decimals) from text
        # Pattern matches: 42, +42, -42, 3.5, +3.5, -3.5
        pattern = r"[+-]?\d+\.?\d*"
        matches = re.findall(pattern, text)

        if not matches:
            # No numeric values found - use 1 as default (for boolean-like mods)
            values = (Decimal("1"),)
        else:
            values = tuple(Decimal(match) for match in matches)

        return cls(type=modifier_type, text=text, values=values, tier=None)
