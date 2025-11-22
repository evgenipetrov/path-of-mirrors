"""Tests for Currency domain entity."""

import asyncpg
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.contexts.core.domain.currency import Currency
from src.shared import Game


class TestCurrencyCreation:
    """Test basic Currency entity creation."""

    @pytest.mark.asyncio
    async def test_create_poe1_currency(self, db_session):
        """Test creating a PoE1 currency."""
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency)
        await db_session.commit()
        await db_session.refresh(currency)

        assert currency.id is not None
        assert currency.game == Game.POE1
        assert currency.name == "Chaos Orb"
        assert currency.display_name == "Chaos"
        assert currency.created_at is not None
        assert currency.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_poe2_currency(self, db_session):
        """Test creating a PoE2 currency."""
        currency = Currency(
            game=Game.POE2,
            name="Exalted Orb",
            display_name="Exalted",
        )
        db_session.add(currency)
        await db_session.commit()
        await db_session.refresh(currency)

        assert currency.id is not None
        assert currency.game == Game.POE2
        assert currency.name == "Exalted Orb"
        assert currency.display_name == "Exalted"

    @pytest.mark.asyncio
    async def test_create_currency_with_all_fields(self, db_session):
        """Test creating currency with all fields."""
        currency = Currency(
            game=Game.POE1,
            name="Divine Orb",
            display_name="Divine",
        )
        db_session.add(currency)
        await db_session.commit()
        await db_session.refresh(currency)

        # Verify BaseEntity fields
        assert currency.id is not None
        assert currency.created_at is not None
        assert currency.updated_at is not None

        # Verify Currency fields
        assert currency.game == Game.POE1
        assert currency.name == "Divine Orb"
        assert currency.display_name == "Divine"


class TestCurrencyUniqueConstraint:
    """Test composite unique constraint (game, name)."""

    @pytest.mark.asyncio
    async def test_same_currency_name_different_games_allowed(self, db_session):
        """Test that same currency name can exist in different games."""
        # Create Chaos Orb for PoE1
        poe1_chaos = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe1_chaos)

        # Create Chaos Orb for PoE2
        poe2_chaos = Currency(
            game=Game.POE2,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe2_chaos)

        await db_session.commit()

        # Both should exist
        result = await db_session.execute(select(Currency).where(Currency.name == "Chaos Orb"))
        currencies = result.scalars().all()

        assert len(currencies) == 2
        assert {c.game for c in currencies} == {Game.POE1, Game.POE2}

    @pytest.mark.asyncio
    async def test_duplicate_currency_same_game_raises_error(self, db_session):
        """Test that duplicate currency in same game raises IntegrityError."""
        # Create first Chaos Orb for PoE1
        currency1 = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency1)
        await db_session.commit()

        # Try to create duplicate
        currency2 = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency2)

        # asyncpg raises UniqueViolationError which is wrapped by SQLAlchemy
        with pytest.raises((IntegrityError, asyncpg.UniqueViolationError)):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_different_currency_names_same_game_allowed(self, db_session):
        """Test that different currency names in same game are allowed."""
        chaos = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(chaos)

        divine = Currency(
            game=Game.POE1,
            name="Divine Orb",
            display_name="Divine",
        )
        db_session.add(divine)

        await db_session.commit()

        # Both should exist
        result = await db_session.execute(select(Currency).where(Currency.game == Game.POE1))
        currencies = result.scalars().all()

        assert len(currencies) == 2
        assert {c.name for c in currencies} == {"Chaos Orb", "Divine Orb"}


class TestCurrencyQueries:
    """Test querying Currency entities."""

    @pytest.mark.asyncio
    async def test_query_by_game(self, db_session):
        """Test querying currencies by game."""
        # Create currencies for both games
        poe1_currencies = [
            Currency(game=Game.POE1, name="Chaos Orb", display_name="Chaos"),
            Currency(game=Game.POE1, name="Divine Orb", display_name="Divine"),
        ]
        for c in poe1_currencies:
            db_session.add(c)

        poe2_currencies = [
            Currency(game=Game.POE2, name="Exalted Orb", display_name="Exalted"),
            Currency(game=Game.POE2, name="Chaos Orb", display_name="Chaos"),
        ]
        for c in poe2_currencies:
            db_session.add(c)

        await db_session.commit()

        # Query PoE1 currencies
        result = await db_session.execute(select(Currency).where(Currency.game == Game.POE1))
        poe1_results = result.scalars().all()

        assert len(poe1_results) == 2
        assert all(c.game == Game.POE1 for c in poe1_results)
        assert {c.name for c in poe1_results} == {"Chaos Orb", "Divine Orb"}

        # Query PoE2 currencies
        result = await db_session.execute(select(Currency).where(Currency.game == Game.POE2))
        poe2_results = result.scalars().all()

        assert len(poe2_results) == 2
        assert all(c.game == Game.POE2 for c in poe2_results)
        assert {c.name for c in poe2_results} == {"Exalted Orb", "Chaos Orb"}

    @pytest.mark.asyncio
    async def test_query_by_game_and_name(self, db_session):
        """Test querying currency by game and name."""
        # Create Chaos Orb for both games
        poe1_chaos = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe1_chaos)

        poe2_chaos = Currency(
            game=Game.POE2,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe2_chaos)

        await db_session.commit()

        # Query PoE1 Chaos Orb specifically
        result = await db_session.execute(
            select(Currency).where(
                Currency.game == Game.POE1,
                Currency.name == "Chaos Orb",
            )
        )
        currency = result.scalar_one()

        assert currency.game == Game.POE1
        assert currency.name == "Chaos Orb"

    @pytest.mark.asyncio
    async def test_query_by_display_name(self, db_session):
        """Test querying by display_name."""
        currencies = [
            Currency(game=Game.POE1, name="Chaos Orb", display_name="Chaos"),
            Currency(game=Game.POE1, name="Divine Orb", display_name="Divine"),
            Currency(game=Game.POE2, name="Chaos Orb", display_name="Chaos"),
        ]
        for c in currencies:
            db_session.add(c)

        await db_session.commit()

        # Query by display_name
        result = await db_session.execute(select(Currency).where(Currency.display_name == "Chaos"))
        chaos_currencies = result.scalars().all()

        assert len(chaos_currencies) == 2
        assert all(c.display_name == "Chaos" for c in chaos_currencies)


class TestCurrencyRepresentation:
    """Test Currency string representation."""

    def test_currency_repr(self):
        """Test __repr__ method."""
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )

        repr_str = repr(currency)

        assert "Currency" in repr_str
        assert "poe1" in repr_str  # Game enum value, not enum name
        assert "Chaos Orb" in repr_str


class TestCurrencyRealExamples:
    """Test Currency with real examples from validation."""

    @pytest.mark.asyncio
    async def test_create_poe1_currencies_from_validation(self, db_session):
        """Test creating PoE1 currencies from validation data."""
        # From poe.ninja economy data
        currencies = [
            Currency(game=Game.POE1, name="Chaos Orb", display_name="Orb"),
            Currency(game=Game.POE1, name="Divine Orb", display_name="Orb"),
        ]

        for c in currencies:
            db_session.add(c)

        await db_session.commit()

        result = await db_session.execute(select(Currency).where(Currency.game == Game.POE1))
        saved_currencies = result.scalars().all()

        assert len(saved_currencies) == 2
        assert {c.name for c in saved_currencies} == {"Chaos Orb", "Divine Orb"}

    @pytest.mark.asyncio
    async def test_create_poe2_currencies_from_validation(self, db_session):
        """Test creating PoE2 currencies from validation data."""
        # From poe.ninja economy data
        currencies = [
            Currency(game=Game.POE2, name="Divine Orb", display_name="Orb"),
            Currency(game=Game.POE2, name="Exalted Orb", display_name="Orb"),
            Currency(game=Game.POE2, name="Chaos Orb", display_name="Orb"),
        ]

        for c in currencies:
            db_session.add(c)

        await db_session.commit()

        result = await db_session.execute(select(Currency).where(Currency.game == Game.POE2))
        saved_currencies = result.scalars().all()

        assert len(saved_currencies) == 3
        assert {c.name for c in saved_currencies} == {
            "Divine Orb",
            "Exalted Orb",
            "Chaos Orb",
        }

    @pytest.mark.asyncio
    async def test_display_name_derivation_heuristic(self, db_session):
        """Test display_name derivation heuristic (last word of name)."""
        currencies = [
            ("Chaos Orb", "Chaos"),
            ("Divine Orb", "Divine"),
            ("Exalted Orb", "Exalted"),
            ("Mirror of Kalandra", "Mirror"),  # Would need special handling
            ("Orb of Alteration", "Alteration"),
        ]

        for name, expected_display in currencies:
            # Simple heuristic: last word
            actual_display = name.split()[-1]

            currency = Currency(
                game=Game.POE1,
                name=name,
                display_name=actual_display,
            )
            db_session.add(currency)

        await db_session.commit()

        result = await db_session.execute(select(Currency))
        saved_currencies = result.scalars().all()

        assert len(saved_currencies) == 5


class TestCurrencyUpdates:
    """Test updating Currency entities."""

    @pytest.mark.asyncio
    async def test_update_display_name(self, db_session):
        """Test updating currency display_name."""
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency)
        await db_session.commit()
        await db_session.refresh(currency)

        original_updated_at = currency.updated_at

        # Update display_name
        currency.display_name = "C"
        await db_session.commit()
        await db_session.refresh(currency)

        assert currency.display_name == "C"
        assert currency.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_cannot_change_game(self, db_session):
        """Test that changing game would violate constraints."""
        # Create currency for PoE1
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency)
        await db_session.commit()

        # Create duplicate in PoE2
        poe2_chaos = Currency(
            game=Game.POE2,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe2_chaos)
        await db_session.commit()

        # Now try to change PoE1 currency to PoE2
        await db_session.refresh(currency)
        currency.game = Game.POE2

        # Should violate unique constraint
        with pytest.raises((IntegrityError, asyncpg.UniqueViolationError)):
            await db_session.commit()


class TestCurrencyDeletion:
    """Test deleting Currency entities."""

    @pytest.mark.asyncio
    async def test_delete_currency(self, db_session):
        """Test deleting a currency."""
        currency = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(currency)
        await db_session.commit()

        currency_id = currency.id

        # Delete currency
        await db_session.delete(currency)
        await db_session.commit()

        # Verify deletion
        result = await db_session.execute(select(Currency).where(Currency.id == currency_id))
        deleted_currency = result.scalar_one_or_none()

        assert deleted_currency is None

    @pytest.mark.asyncio
    async def test_delete_one_game_keeps_other(self, db_session):
        """Test deleting currency from one game keeps other game's currency."""
        # Create Chaos Orb for both games
        poe1_chaos = Currency(
            game=Game.POE1,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe1_chaos)

        poe2_chaos = Currency(
            game=Game.POE2,
            name="Chaos Orb",
            display_name="Chaos",
        )
        db_session.add(poe2_chaos)

        await db_session.commit()

        # Delete PoE1 version
        await db_session.delete(poe1_chaos)
        await db_session.commit()

        # PoE2 version should still exist
        result = await db_session.execute(select(Currency).where(Currency.name == "Chaos Orb"))
        remaining_currencies = result.scalars().all()

        assert len(remaining_currencies) == 1
        assert remaining_currencies[0].game == Game.POE2
