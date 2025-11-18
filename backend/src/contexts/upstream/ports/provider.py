"""Provider interface for game-specific data sources.

Epic 1.1: Define the contract without imposing structure.
Epic 1.2: Implement real poe.ninja clients.
Epic 1.3: Add canonical schemas and normalization.

Design Philosophy:
- Return raw dictionaries for now - canonical models come in Epic 1.3
- This keeps us flexible as we learn the actual poe.ninja structures
- Don't abstract what we don't understand yet (YAGNI principle)
"""

from typing import Any, Protocol

from src.shared import Game


class BaseProvider(Protocol):
    """Minimal interface for fetching game-specific data.

    Implementations fetch data from external sources (poe.ninja, etc.)
    and return raw data structures. Normalization happens in Epic 1.4.

    Epic 1.1: Protocol definition with stub implementations
    Epic 1.2: Real HTTP client implementations
    Epic 1.3: Add return type models (Pydantic)
    """

    @property
    def game(self) -> Game:
        """Which game this provider serves.

        Returns:
            Game enum (POE1 or POE2)
        """
        ...

    async def get_active_leagues(self) -> list[dict[str, Any]]:
        """Fetch active leagues for this game.

        Returns:
            List of league info dicts with at minimum:
            - name: str (league name)
            - active: bool (whether league is active)

            Additional fields TBD based on actual API response.

        Note:
            Epic 1.1: Stub returns hardcoded data
            Epic 1.2: Real implementation fetches from poe.ninja
        """
        ...

    async def fetch_economy_snapshot(
        self,
        league: str,
        category: str,
    ) -> dict[str, Any]:
        """Fetch economy data for a league/category.

        Args:
            league: League name (e.g., "Settlers", "Standard")
            category: Category name (e.g., "Currency", "Fragments")

        Returns:
            Raw economy snapshot dict from provider.
            Structure TBD based on poe.ninja API response.

        Note:
            Epic 1.1: Stub returns minimal data
            Epic 1.2: Real implementation fetches from poe.ninja
            Epic 1.3: Return type becomes CanonicalEconomySnapshot
        """
        ...

    async def fetch_build_ladder(
        self,
        league: str,
    ) -> dict[str, Any]:
        """Fetch build ladder data for a league.

        Args:
            league: League name (e.g., "Settlers", "Standard")

        Returns:
            Raw build ladder dict from provider.
            Structure TBD based on poe.ninja API response.

        Note:
            Epic 1.1: Stub returns minimal data
            Epic 1.2: Real implementation fetches from poe.ninja
            Epic 1.3: Return type becomes CanonicalBuildLadder
        """
        ...
