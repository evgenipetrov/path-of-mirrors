"""Core domain context - shared domain concepts.

This context contains base models and domain entities
that are shared across multiple bounded contexts.

Exports:
    - Base entity models (BaseEntity, mixins)
    - Domain entities (League, Currency, Item)
    - Domain value objects (Modifier)
    - Domain enumerations (LeagueType, ModifierType)
    - Domain constants (ItemRarity)
"""

from .domain.base import BaseEntity, TimestampMixin, UUIDPrimaryKeyMixin
from .domain.build import Build
from .domain.currency import Currency
from .domain.enums import League as LeagueType
from .domain.item import Item, ItemRarity
from .domain.league import League
from .domain.modifier import Modifier, ModifierType

__all__ = [
    # Base models and mixins
    "BaseEntity",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    # Domain entities
    "Build",
    "Currency",
    "Item",
    "League",
    # Value objects
    "Modifier",
    # Enumerations
    "LeagueType",  # Renamed to avoid conflict with League entity
    "ModifierType",
    # Constants
    "ItemRarity",
]
