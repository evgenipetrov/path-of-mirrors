"""Tests for provider implementations.

Epic 1.1: Test stub providers return expected data structures.
"""

import pytest

from src.contexts.upstream.adapters import PoE1Provider, PoE2Provider
from src.shared import Game


class TestPoE1Provider:
    """Test PoE1 stub provider."""

    @pytest.fixture
    def provider(self):
        """Create PoE1Provider instance."""
        return PoE1Provider()

    def test_game_property_returns_poe1(self, provider):
        """Provider should identify as POE1."""
        assert provider.game == Game.POE1

    @pytest.mark.asyncio
    async def test_get_active_leagues_returns_list(self, provider):
        """Should return list of league dicts."""
        leagues = await provider.get_active_leagues()

        assert isinstance(leagues, list)
        assert len(leagues) > 0
        # Check first league has expected structure
        assert "name" in leagues[0]
        assert "active" in leagues[0]

    @pytest.mark.asyncio
    async def test_get_active_leagues_includes_standard(self, provider):
        """Should include Standard league."""
        leagues = await provider.get_active_leagues()

        league_names = [league["name"] for league in leagues]
        assert "Standard" in league_names

    @pytest.mark.asyncio
    async def test_fetch_economy_snapshot_returns_dict(self, provider):
        """Should return economy snapshot dict."""
        snapshot = await provider.fetch_economy_snapshot(
            league="Settlers",
            category="Currency",
        )

        assert isinstance(snapshot, dict)
        assert snapshot["league"] == "Settlers"
        assert snapshot["category"] == "Currency"
        assert "lines" in snapshot
        assert snapshot["stub"] is True

    @pytest.mark.asyncio
    async def test_fetch_build_ladder_returns_dict(self, provider):
        """Should return build ladder dict."""
        ladder = await provider.fetch_build_ladder(league="Settlers")

        assert isinstance(ladder, dict)
        assert ladder["league"] == "Settlers"
        assert "builds" in ladder
        assert ladder["stub"] is True


class TestPoE2Provider:
    """Test PoE2 stub provider."""

    @pytest.fixture
    def provider(self):
        """Create PoE2Provider instance."""
        return PoE2Provider()

    def test_game_property_returns_poe2(self, provider):
        """Provider should identify as POE2."""
        assert provider.game == Game.POE2

    @pytest.mark.asyncio
    async def test_get_active_leagues_returns_list(self, provider):
        """Should return list of league dicts."""
        leagues = await provider.get_active_leagues()

        assert isinstance(leagues, list)
        assert len(leagues) > 0
        # Check first league has expected structure
        assert "name" in leagues[0]
        assert "active" in leagues[0]

    @pytest.mark.asyncio
    async def test_fetch_economy_snapshot_returns_dict(self, provider):
        """Should return economy snapshot dict."""
        snapshot = await provider.fetch_economy_snapshot(
            league="Standard",
            category="Currency",
        )

        assert isinstance(snapshot, dict)
        assert snapshot["league"] == "Standard"
        assert snapshot["category"] == "Currency"
        assert "lines" in snapshot
        assert snapshot["stub"] is True

    @pytest.mark.asyncio
    async def test_fetch_build_ladder_returns_dict(self, provider):
        """Should return build ladder dict."""
        ladder = await provider.fetch_build_ladder(league="Standard")

        assert isinstance(ladder, dict)
        assert ladder["league"] == "Standard"
        assert "builds" in ladder
        assert ladder["stub"] is True
