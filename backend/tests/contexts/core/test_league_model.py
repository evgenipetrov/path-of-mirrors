"""Tests for League core domain model.

Validates that the League model can represent data from all upstream sources.
Uses inline fixtures to avoid dependency on gitignored sample files.
"""

import pytest

from src.contexts.core import League
from src.shared import Game


class TestLeagueModel:
    """Test suite for League entity."""

    def test_league_creation_minimal(self):
        """Test creating a league with required fields."""
        league = League(
            game=Game.POE1,
            name="Keepers of the Flame",
            display_name="Keepers",
        )

        assert league.game == Game.POE1
        assert league.name == "Keepers of the Flame"
        assert league.display_name == "Keepers"

    def test_standard_league(self):
        """Test Standard league creation."""
        league = League(
            game=Game.POE1,
            name="Standard",
            display_name="Standard",
        )

        assert league.name == "Standard"

    def test_poe2_league(self):
        """Test PoE2 league creation."""
        league = League(
            game=Game.POE2,
            name="Rise of the Abyssal",
            display_name="Rise of the Abyssal",
        )

        assert league.game == Game.POE2


class TestLeagueFromUpstreamStructures:
    """Test League model against upstream data structures.

    Uses inline fixtures representing real poe.ninja API responses.
    """

    @pytest.fixture
    def poe1_index_state_mock(self):
        """Mock poe.ninja index state response for PoE1."""
        return {
            "economyLeagues": [
                {
                    "name": "Keepers of the Flame",
                    "url": "keepers",
                    "displayName": "Keepers",
                },
                {
                    "name": "Hardcore Keepers",
                    "url": "keepershc",
                    "displayName": "HC Keepers",
                },
                {
                    "name": "Standard",
                    "url": "standard",
                    "displayName": "Standard",
                },
            ],
            "oldEconomyLeagues": [
                {
                    "name": "Settlers of Kalguur",
                    "url": "settlers",
                    "displayName": "Settlers",
                },
                {
                    "name": "Crucible",
                    "url": "crucible",
                    "displayName": "Crucible",
                },
            ],
        }

    @pytest.fixture
    def poe2_index_state_mock(self):
        """Mock poe.ninja index state response for PoE2."""
        return {
            "economyLeagues": [
                {
                    "name": "Early Access Standard",
                    "url": "early_access_standard",
                    "displayName": "Standard EA",
                },
                {
                    "name": "Early Access Hardcore",
                    "url": "early_access_hardcore",
                    "displayName": "Hardcore EA",
                },
            ],
            "oldEconomyLeagues": [],
        }

    def test_from_poe1_index_state(self, poe1_index_state_mock):
        """Validate League can represent poe.ninja index state data.

        Note: Only active leagues are tracked. Old leagues are ignored.
        Note: poe.ninja's 'url' field is adapter-specific and not stored in core.
        """
        data = poe1_index_state_mock

        # Validate active economy leagues can be modeled
        for league_data in data["economyLeagues"]:
            league = League(
                game=Game.POE1,
                name=league_data["name"],
                display_name=league_data["displayName"],
            )

            assert league.name == league_data["name"]
            assert league.display_name == league_data["displayName"]

    def test_from_poe2_index_state(self, poe2_index_state_mock):
        """Validate League can represent PoE2 poe.ninja index state data.

        Note: Only active leagues are tracked.
        Note: poe.ninja's 'url' field is adapter-specific and not stored in core.
        """
        data = poe2_index_state_mock

        # Validate PoE2 leagues
        for league_data in data["economyLeagues"]:
            league = League(
                game=Game.POE2,
                name=league_data["name"],
                display_name=league_data["displayName"],
            )

            assert league.game == Game.POE2
            assert league.name == league_data["name"]
