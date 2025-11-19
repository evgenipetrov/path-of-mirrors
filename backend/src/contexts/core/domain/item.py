"""Item domain model.

Items are the core entity in Path of Exile - everything from equipment to currency
to maps. This model represents items from various sources (Trade API, poe.ninja, PoB).

Design Philosophy:
    - Store enough detail to be useful for analysis and display
    - Don't replicate entire game database (that's what upstream sources are for)
    - Focus on fields needed for economic analysis and build recommendations
"""

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared import Game

from .base import BaseEntity


class ItemRarity(str):
    """Item rarity levels.

    Note: Not using Enum to allow flexibility for future rarity types.
    """
    NORMAL = "Normal"
    MAGIC = "Magic"
    RARE = "Rare"
    UNIQUE = "Unique"


class Item(BaseEntity):
    """Represents a Path of Exile item.

    Items can be equipment, currency, maps, fragments, etc. This model stores
    the essential fields needed for economic analysis and build recommendations.

    Key Design Decisions:
        - Modifiers stored as JSONB array (using Modifier.to_dict())
        - No FK to Currency - currency context comes from pricing/market data
        - game + name + base_type composite provides natural grouping
        - Flexible enough to handle PoE1 and PoE2 differences

    Examples:
        - Equipment: "Prismatic Ring" with explicit mods
        - Unique: "Headhunter" (Leather Belt)
        - Currency: "Divine Orb"
        - Map: "Ivory Temple Map"
    """

    __tablename__ = "items"

    # Required fields (no defaults - must come first for dataclass)
    # Identity
    game: Mapped[Game] = mapped_column(String(10), index=True)
    # "Spidersilk Robe" (base type display)
    type_line: Mapped[str] = mapped_column(String(200))
    # "Spidersilk Robe" (for grouping)
    base_type: Mapped[str] = mapped_column(String(200), index=True)
    # "Normal", "Magic", "Rare", "Unique"
    rarity: Mapped[str] = mapped_column(String(20))

    # Optional fields (with defaults - must come after required fields)
    # "Soul Mantle" or None for non-uniques
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    # ilvl (84, etc.)
    item_level: Mapped[int | None] = mapped_column(nullable=True, default=None)
    # "Body Armours", "Rings", "Maps"
    item_class: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    # Modifiers (stored as JSONB array) - each element is Modifier.to_dict() output
    implicit_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    explicit_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    crafted_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    enchant_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    fractured_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    crucible_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)
    scourge_mods: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)

    # Equipment-specific fields
    sockets: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Additional properties (flexible JSONB for source-specific data)
    # Can store: requirements, properties, influence, etc.
    properties: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    def __repr__(self) -> str:
        """String representation."""
        display_name = self.name if self.name else self.type_line
        return f"<Item(game={self.game}, name='{display_name}', rarity={self.rarity})>"


# Indexes for common queries
Index("ix_item_game_base_type", Item.game, Item.base_type)  # Group by base type
Index("ix_item_game_rarity", Item.game, Item.rarity)  # Filter by rarity
Index("ix_item_name", Item.name)  # Search by name (unique items)
