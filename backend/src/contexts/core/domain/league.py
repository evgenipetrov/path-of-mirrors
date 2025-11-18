"""League domain model.

A League represents a Path of Exile game mode/competition.
Examples: "Keepers of the Flame", "Standard", "Settlers of Kalguur".

Leagues are foundational - economy data, character builds, and trade listings
all reference a specific league. This model only tracks active softcore trade leagues.
"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared import Game

from .base import BaseEntity


class League(BaseEntity):
    """Represents a Path of Exile league (temp league or permanent).

    Leagues are game-specific competitions/economies that run for a period of time.

    Design:
        - One row per (game, league_name) combination
        - Mutable - leagues can become inactive, dates can be updated
        - Source of truth for "which leagues exist for which game"
    """

    __tablename__ = "leagues"

    # Identity (composite unique: game + name)
    game: Mapped[Game] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(100))  # "Keepers of the Flame"

    # Display
    display_name: Mapped[str] = mapped_column(String(150))  # "Keepers" (UI display)

    def __repr__(self) -> str:
        """String representation."""
        return f"<League(game={self.game}, name='{self.name}')>"


# Composite unique constraint
Index(
    "ix_league_game_name",
    League.game,
    League.name,
    unique=True,
)
