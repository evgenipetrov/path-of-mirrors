"""Core domain enumerations shared across contexts.

Centralizes common enums used by multiple bounded contexts.
These represent fixed sets of values in the domain model.
"""

from enum import Enum


class League(str, Enum):
    """Path of Exile league categories.

    Distinguishes between permanent and temporary leagues.
    """

    STANDARD = "standard"
    CURRENT = "current"  # Active temporary league

    def __str__(self) -> str:
        """Return string value."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable league category name."""
        return {
            League.STANDARD: "Standard",
            League.CURRENT: "Current League",
        }[self]
