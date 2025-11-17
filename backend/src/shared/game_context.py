"""Game context enumeration for PoE1 and PoE2."""

from enum import Enum


class Game(str, Enum):
    """Supported Path of Exile games."""

    POE1 = "poe1"
    POE2 = "poe2"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @property
    def display_name(self) -> str:
        """Return human-readable game name."""
        return "Path of Exile 1" if self == Game.POE1 else "Path of Exile 2"
