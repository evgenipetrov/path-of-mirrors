"""Core domain context - shared domain concepts.

This context contains base models and domain entities
that are shared across multiple bounded contexts.

Exports:
    - Base entity models (BaseEntity, mixins)
    - Domain entities (League)
    - Domain enumerations (LeagueType)
"""

from .domain.base import BaseEntity, TimestampMixin, UUIDPrimaryKeyMixin
from .domain.enums import League as LeagueType
from .domain.league import League

__all__ = [
    # Base models and mixins
    "BaseEntity",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    # Domain entities
    "League",
    # Enumerations
    "LeagueType",  # Renamed to avoid conflict with League entity
]
