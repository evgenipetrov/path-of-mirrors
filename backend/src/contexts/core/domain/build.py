"""Build domain model.

A Build represents a Path of Exile character configuration - the combination of
passive tree, items, gems, and character attributes that define a playable character.

Builds can come from multiple sources:
- Path of Building (XML exports)
- poe.ninja (build snapshots from ladder)
- User-created builds in the application

Design Philosophy:
    - Store complete build snapshot for analysis
    - Support both PoE1 and PoE2
    - Enable build cost calculations (market context)
    - Enable build recommendations (builds context)
    - Flexible enough for different sources (PoB vs poe.ninja vs custom)
"""

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared import Game

from .base import BaseEntity


class Build(BaseEntity):
    """Represents a Path of Exile character build.

    A build is a complete character configuration including items, passive tree,
    gems, and other character attributes. Builds can be imported from PoB,
    scraped from poe.ninja, or created by users.

    Key Design Decisions:
        - Items stored as array of item references (UUIDs) or embedded item data
        - Passive tree stored as JSONB (node allocations)
        - Gems stored as JSONB array (skill gems + links)
        - No direct FK to League (league context via name)
        - Supports both PoE1 and PoE2 with flexible schema
        - Source tracking (pob, poeninja, user) for provenance

    Examples:
        - PoB import: "Level 92 RF Juggernaut"
        - poe.ninja snapshot: "#1 Necromancer SSF HC"
        - User build: "Budget SSF Starter"

    Attributes:
        game: Game context (PoE1 or PoE2)
        name: Build name/title (user-provided or derived)
        character_class: Base class (e.g., "Witch", "Templar")
        ascendancy: Ascendancy class (e.g., "Necromancer", "Juggernaut")
        level: Character level (1-100)
        league: League name (e.g., "Standard", "Affliction")

        # Character stats (derived or stored)
        life: Total life
        energy_shield: Total ES
        mana: Total mana
        armour: Total armour
        evasion: Total evasion

        # Build components (JSONB)
        passive_tree: Passive tree node allocations and jewels
        items: Equipped items (references or embedded data)
        skills: Active skills with gem links

        # Metadata
        source: Build source ("pob", "poeninja", "user")
        source_url: Original URL if imported
        author: Build creator (username or account name)
        notes: User notes or description
        properties: Flexible JSONB for source-specific data
    """

    __tablename__ = "builds"

    # Required fields (no defaults - must come first for dataclass)
    # Game and identity
    game: Mapped[Game] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(200))
    character_class: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer)

    # Optional fields (with defaults)
    # Character specialization
    ascendancy: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    league: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    # Core character stats (nullable - may not be available from all sources)
    life: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    energy_shield: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    mana: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    armour: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    evasion: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Build components (JSONB)
    # Passive tree: {"nodes": [12345, 23456, ...], "jewels": {...}, "masteries": {...}}
    passive_tree: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Items: Could be:
    # - Array of Item UUIDs: ["uuid1", "uuid2", ...]
    # - Embedded item data: [{"slot": "weapon", "item": {...}}, ...]
    # - Mixed approach depending on source
    items: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Skills: [{"name": "Raise Spectre", "gems": [...], "links": 6}, ...]
    skills: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=None)

    # Metadata and provenance
    source: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Additional flexible data (DPS calculations, config options, etc.)
    properties: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Build(game={self.game}, name='{self.name}', "
            f"class={self.character_class}, level={self.level})>"
        )


# Indexes for common queries
# Search by game + class
Index("ix_build_game_class", Build.game, Build.character_class)
# Search by game + ascendancy
Index("ix_build_game_ascendancy", Build.game, Build.ascendancy)
# Search by game + league
Index("ix_build_game_league", Build.game, Build.league)
# Search by source (for data quality checks)
Index("ix_build_source", Build.source)
# Search by level range
Index("ix_build_level", Build.level)
