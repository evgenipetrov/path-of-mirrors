"""Tests for Currency core domain model.

Validates that the Currency model can represent data from all upstream sources.
Uses inline fixtures to avoid dependency on gitignored sample files.
"""

import pytest

from src.contexts.core import Currency
from src.shared import Game


class TestCurrencyModel:
    """Test suite for Currency entity."""

    def test_currency_creation_minimal(self):
        """Test creating a currency with required fields."""
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )

        assert currency.game == Game.POE1
        assert currency.name == "Chaos Orb"
        assert currency.display_name == "Chaos"

    def test_poe1_currency(self):
        """Test PoE1 currency creation."""
        currency = Currency(
            game=Game.POE1,
            name="Divine Orb",
            display_name="Divine",
        )

        assert currency.game == Game.POE1
        assert currency.name == "Divine Orb"

    def test_poe2_currency(self):
        """Test PoE2 currency creation."""
        currency = Currency(
            game=Game.POE2,
            name="Exalted Orb",
            display_name="Exalted",
        )

        assert currency.game == Game.POE2
        assert currency.name == "Exalted Orb"


class TestCurrencyFromUpstreamStructures:
    """Test Currency model against upstream data structures.

    Uses inline fixtures representing real poe.ninja API responses.
    """

    @pytest.fixture
    def poe1_currency_core_mock(self):
        """Mock poe.ninja currency core response for PoE1."""
        return {
            "items": [
                {
                    "id": "chaos",
                    "name": "Chaos Orb",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lSZXJvbGxSYXJlIiwic2NhbGUiOjF9XQ/46a2347805/CurrencyRerollRare.png",
                    "category": "Currency",
                    "detailsId": "chaos-orb",
                },
                {
                    "id": "divine",
                    "name": "Divine Orb",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lNb2RWYWx1ZXMiLCJzY2FsZSI6MX1d/ec48896769/CurrencyModValues.png",
                    "category": "Currency",
                    "detailsId": "divine-orb",
                },
                {
                    "id": "mirror",
                    "name": "Mirror of Kalandra",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lEdXBsaWNhdGUiLCJzY2FsZSI6MX1d/7111e35254/CurrencyDuplicate.png",
                    "category": "Currency",
                    "detailsId": "mirror-of-kalandra",
                },
            ],
            "rates": {"divine": 0.008322},
            "primary": "chaos",
            "secondary": "divine",
        }

    @pytest.fixture
    def poe2_currency_core_mock(self):
        """Mock poe.ninja currency core response for PoE2."""
        return {
            "items": [
                {
                    "id": "divine",
                    "name": "Divine Orb",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lNb2RWYWx1ZXMiLCJzY2FsZSI6MSwicmVhbG0iOiJwb2UyIn1d/2986e220b3/CurrencyModValues.png",
                    "category": "Currency",
                    "detailsId": "divine-orb",
                },
                {
                    "id": "exalted",
                    "name": "Exalted Orb",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lBZGRNb2RUb1JhcmUiLCJzY2FsZSI6MSwicmVhbG0iOiJwb2UyIn1d/ad7c366789/CurrencyAddModToRare.png",
                    "category": "Currency",
                    "detailsId": "exalted-orb",
                },
                {
                    "id": "chaos",
                    "name": "Chaos Orb",
                    "image": "/gen/image/WzI1LDE0LHsiZiI6IjJESXRlbXMvQ3VycmVuY3kvQ3VycmVuY3lSZXJvbGxSYXJlIiwic2NhbGUiOjEsInJlYWxtIjoicG9lMiJ9XQ/c0ca392a78/CurrencyRerollRare.png",
                    "category": "Currency",
                    "detailsId": "chaos-orb",
                },
            ],
            "rates": {"exalted": 1808, "chaos": 50.03},
            "primary": "divine",
            "secondary": "chaos",
        }

    def test_from_poe1_currency_core(self, poe1_currency_core_mock):
        """Validate Currency can represent poe.ninja currency data.

        Note: poe.ninja's 'id', 'image', 'detailsId' fields are adapter-specific
              and not stored in core domain.
        Note: 'rates', 'primary', 'secondary' are pricing metadata, not currency attributes.
        """
        data = poe1_currency_core_mock

        # Validate core currencies can be modeled
        for currency_data in data["items"]:
            # For display_name, we use the last word of the name (e.g., "Chaos Orb" -> "Chaos")
            display_name = currency_data["name"].split()[-1]

            currency = Currency(
                game=Game.POE1,
                name=currency_data["name"],
                display_name=display_name,
            )

            assert currency.name == currency_data["name"]
            assert currency.display_name == display_name

        # Verify specific currencies
        chaos = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        assert chaos.name == "Chaos Orb"

    def test_from_poe2_currency_core(self, poe2_currency_core_mock):
        """Validate Currency can represent PoE2 poe.ninja currency data.

        Note: poe.ninja's 'id', 'image', 'detailsId' fields are adapter-specific
              and not stored in core domain.
        Note: PoE2 uses Divine as primary currency (not Chaos like PoE1).
        """
        data = poe2_currency_core_mock

        # Validate PoE2 currencies
        for currency_data in data["items"]:
            # For display_name, we use the last word of the name
            display_name = currency_data["name"].split()[-1]

            currency = Currency(
                game=Game.POE2,
                name=currency_data["name"],
                display_name=display_name,
            )

            assert currency.game == Game.POE2
            assert currency.name == currency_data["name"]

        # Verify PoE2 uses Divine as primary
        assert data["primary"] == "divine"
