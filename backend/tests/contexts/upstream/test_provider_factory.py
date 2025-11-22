"""Tests for provider factory pattern.

Epic 1.1: Test factory returns correct provider for each game.
"""

from src.contexts.upstream.adapters import PoE1Provider, PoE2Provider, get_provider
from src.shared import Game


class TestProviderFactory:
    """Test the get_provider factory function."""

    def test_get_provider_returns_poe1_provider(self):
        """Factory should return PoE1Provider for POE1 game."""
        provider = get_provider(Game.POE1)

        assert isinstance(provider, PoE1Provider)
        assert provider.game == Game.POE1

    def test_get_provider_returns_poe2_provider(self):
        """Factory should return PoE2Provider for POE2 game."""
        provider = get_provider(Game.POE2)

        assert isinstance(provider, PoE2Provider)
        assert provider.game == Game.POE2

    def test_get_provider_returns_new_instance_each_time(self):
        """Factory should return new instances (stateless providers)."""
        provider1 = get_provider(Game.POE1)
        provider2 = get_provider(Game.POE1)

        assert provider1 is not provider2
        assert isinstance(provider1, PoE1Provider)
        assert isinstance(provider2, PoE1Provider)
