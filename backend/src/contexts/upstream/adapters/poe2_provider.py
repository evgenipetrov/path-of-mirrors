"""Path of Exile 2 data provider implementation.

Epic 1.1: Stub implementation with hardcoded data
Epic 1.2: Real poe.ninja HTTP client integration
"""

from typing import Any

from src.shared import Game


class PoE2Provider:
    """Stub provider for Path of Exile 2.

    Epic 1.1: Returns static test data for validation.
    Epic 1.2: Replace with real poe.ninja HTTP client.

    Design:
        - Minimal implementation to test the provider pattern
        - Returns hardcoded data structures
        - No HTTP calls, no external dependencies
    """

    @property
    def game(self) -> Game:
        """Return POE2 game identifier."""
        return Game.POE2

    async def get_active_leagues(self) -> list[dict[str, Any]]:
        """Return hardcoded PoE2 leagues.

        Epic 1.1: Static data for testing
        Epic 1.2: Fetch from poe.ninja index-state endpoint

        Returns:
            List of league info dicts with:
            - name: League name
            - active: Whether league is currently active

        Note:
            PoE2 has different league names than PoE1.
            As of Nov 2024, PoE2 is in early access.
        """
        return [
            {"name": "Standard", "active": True},
            {"name": "Hardcore", "active": True},
        ]

    async def fetch_economy_snapshot(
        self,
        league: str,
        category: str,
    ) -> dict[str, Any]:
        """Return stub economy data.

        Epic 1.1: Minimal stub for testing
        Epic 1.2: Fetch from poe.ninja economy endpoints
        Epic 1.3: Parse into canonical models

        Args:
            league: League name (e.g., "Standard")
            category: Category name (e.g., "Currency")

        Returns:
            Stub economy snapshot with:
            - league: Echoed league name
            - category: Echoed category name
            - lines: Empty list (populated in Epic 1.2)
            - stub: True (indicates this is test data)

        Note:
            PoE2 economy categories may differ from PoE1.
            Epic 1.2 will handle these differences.
        """
        return {
            "league": league,
            "category": category,
            "lines": [],  # Will contain price data in Epic 1.2
            "stub": True,
        }

    async def fetch_build_ladder(
        self,
        league: str,
    ) -> dict[str, Any]:
        """Return stub build ladder data.

        Epic 1.1: Minimal stub for testing
        Epic 1.2: Fetch from poe.ninja builds endpoints
        Epic 1.3: Parse into canonical models

        Args:
            league: League name (e.g., "Standard")

        Returns:
            Stub build ladder with:
            - league: Echoed league name
            - builds: Empty list (populated in Epic 1.2)
            - stub: True (indicates this is test data)

        Note:
            PoE2 build structure differs significantly from PoE1.
            Epic 1.3 will define canonical models to handle both.
        """
        return {
            "league": league,
            "builds": [],  # Will contain build data in Epic 1.2
            "stub": True,
        }
