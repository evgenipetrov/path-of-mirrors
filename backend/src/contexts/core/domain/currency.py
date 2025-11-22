"""Currency domain model.

Currencies are the fundamental unit of value in Path of Exile's economy.
All item prices are expressed relative to currencies (e.g., Chaos Orb, Divine Orb).
"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.contexts.core.domain.base import BaseEntity
from src.shared import Game


class Currency(BaseEntity):
    """Represents a Path of Exile currency item.

    Currencies are the fundamental unit of value in PoE economy.
    All item prices are expressed relative to currencies.

    Examples:
        - PoE1: Chaos Orb, Divine Orb, Mirror of Kalandra
        - PoE2: Exalted Orb, Divine Orb, Chaos Orb

    Attributes:
        game: The game this currency belongs to (PoE1 or PoE2)
        name: Full currency name (e.g., "Chaos Orb")
        display_name: Short display name for UI (e.g., "Chaos")
    """

    __tablename__ = "currencies"  # type: ignore[misc]

    # Identity (composite unique: game + name)
    game: Mapped[Game] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(100))  # "Chaos Orb"

    # Display
    display_name: Mapped[str] = mapped_column(String(50))  # "Chaos"

    def __repr__(self) -> str:
        """String representation."""
        return f"<Currency(game={self.game}, name='{self.name}')>"


# Composite unique constraint: one currency name per game
Index("ix_currency_game_name", Currency.game, Currency.name, unique=True)
