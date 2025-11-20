"""Integration test for PoB parser + Trade API + Upgrade Ranker flow.

This test validates the end-to-end flow:
1. Parse PoB XML
2. Extract item type from parsed build
3. Search for similar items on Trade API
4. Rank upgrades and calculate scores

NOTE: This uses mocked responses to avoid hitting the real Trade API.
For manual testing with real API, use the script in scripts/manual_trade_test.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.contexts.upstream.services.pob_parser import parse_pob_xml
from src.contexts.upstream.services.trade_api_client import search_and_fetch_items, build_simple_query
from src.contexts.upstream.services.upgrade_ranker import rank_upgrades
from src.shared import Game


# Sample PoB XML with a simple character
SAMPLE_POB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<PathOfBuilding>
    <Build level="90" targetVersion="3_0" bandit="None" className="Necromancer" ascendClassName="Occultist" mainSocketGroup="1">
        <PlayerStat stat="Life" value="5000"/>
        <PlayerStat stat="EnergyShield" value="3000"/>
    </Build>
    <Items activeItemSet="1">
        <ItemSet id="1">
            <Slot name="Amulet" itemId="1"/>
        </ItemSet>
        <Item id="1">
Jade Amulet
Rarity: Rare
Corruption Choker
Requirements:
Level: 60
Implicits: 1
+25 to Dexterity
+80 to maximum Life
+45% to Fire Resistance
+32% to Cold Resistance
        </Item>
    </Items>
</PathOfBuilding>
"""


class TestPoBTradeIntegration:
    """Test integration between PoB parser and Trade API."""

    @pytest.mark.asyncio
    async def test_parse_pob_and_search_for_item(self):
        """Test parsing PoB and searching for similar item on Trade API."""
        # Step 1: Parse PoB XML
        parsed_build = parse_pob_xml(SAMPLE_POB_XML, Game.POE1)

        # Verify we got a build with items
        assert parsed_build.name is not None
        assert parsed_build.items is not None
        assert "Amulet" in parsed_build.items

        # Step 2: Extract item type from parsed build
        amulet = parsed_build.items["Amulet"]
        assert amulet["base_type"] == "Jade Amulet"

        # Step 3: Build Trade API query based on item
        # In this test, we'll search for Jade Amulets with life
        query = build_simple_query(
            item_type=amulet["base_type"],
            min_life=60,  # Lower than the item's 80 life
            max_price_chaos=50,
        )

        # Mock Trade API responses
        search_response = MagicMock()
        search_response.json.return_value = {
            "result": ["trade1", "trade2", "trade3"],
            "total": 100,
        }

        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": [
                {
                    "id": "trade1",
                    "item": {
                        "name": "Death Coil",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                    },
                    "listing": {
                        "price": {"amount": 25, "currency": "chaos"},
                    },
                },
                {
                    "id": "trade2",
                    "item": {
                        "name": "Grim Locket",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                    },
                    "listing": {
                        "price": {"amount": 30, "currency": "chaos"},
                    },
                },
            ]
        }

        # Step 4: Search Trade API with mocked client
        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=search_response)
            mock_client.get = AsyncMock(return_value=fetch_response)
            mock_get_client.return_value = mock_client

            # Search for items
            items = await search_and_fetch_items(
                Game.POE1,
                "Standard",
                query,
                limit=10,
            )

            # Verify we got results
            assert len(items) == 2
            assert items[0]["item"]["baseType"] == "Jade Amulet"
            assert items[0]["listing"]["price"]["currency"] == "chaos"

            # Verify both search and fetch were called
            assert mock_client.post.call_count == 1
            assert mock_client.get.call_count == 1

    def test_extract_item_search_params_from_pob(self):
        """Test extracting search parameters from PoB item."""
        # Parse PoB
        parsed_build = parse_pob_xml(SAMPLE_POB_XML, Game.POE1)

        # Get the amulet
        amulet = parsed_build.items["Amulet"]

        # Extract base type for search
        assert amulet["base_type"] == "Jade Amulet"

        # Extract modifiers for filtering
        assert amulet["explicit_mods"] is not None
        assert "+80 to maximum Life" in amulet["explicit_mods"]

        # Build query
        query = build_simple_query(
            item_type=amulet["base_type"],
            min_life=60,  # Search for items with at least 60 life
        )

        # Verify query structure
        assert query["query"]["type"] == "Jade Amulet"
        assert query["query"]["stats"][0]["filters"][0]["id"] == "pseudo.pseudo_total_life"
        assert query["query"]["stats"][0]["filters"][0]["value"]["min"] == 60


class TestFullUpgradeFlow:
    """Test the complete end-to-end upgrade finder flow."""

    @pytest.mark.asyncio
    async def test_full_pob_to_ranked_upgrades(self):
        """Test complete flow: PoB → Trade API → Ranking → Results."""
        # Step 1: Parse PoB build
        parsed_build = parse_pob_xml(SAMPLE_POB_XML, Game.POE1)
        current_amulet = parsed_build.items["Amulet"]

        # Step 2: Build Trade API query
        query = build_simple_query(
            item_type=current_amulet["base_type"],
            min_life=60,
            max_price_chaos=100,
        )

        # Step 3: Mock Trade API responses with realistic item data
        search_response = MagicMock()
        search_response.json.return_value = {
            "result": ["upgrade1", "upgrade2", "upgrade3"],
            "total": 3,
        }

        # Mock fetch with items that are actual upgrades
        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": [
                {
                    "id": "upgrade1",
                    "item": {
                        "name": "Death Coil",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                        # Parse these into PoB format for upgrade ranker
                    },
                    "listing": {
                        "price": {"amount": 25, "currency": "chaos"},
                    },
                },
                {
                    "id": "upgrade2",
                    "item": {
                        "name": "Grim Locket",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                    },
                    "listing": {
                        "price": {"amount": 50, "currency": "chaos"},
                    },
                },
                {
                    "id": "upgrade3",
                    "item": {
                        "name": "Doom Loop",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                    },
                    "listing": {
                        "price": {"amount": 75, "currency": "chaos"},
                    },
                },
            ]
        }

        # Step 4: Search Trade API
        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=search_response)
            mock_client.get = AsyncMock(return_value=fetch_response)
            mock_get_client.return_value = mock_client

            trade_items = await search_and_fetch_items(
                Game.POE1,
                "Standard",
                query,
                limit=10,
            )

        # Verify we got trade results
        assert len(trade_items) == 3

        # Step 5: Convert trade items to PoB format for ranking
        # For MVP, we'll create mock candidate items with better stats
        candidate_items = [
            {
                # Better life, same resistances
                "base_type": "Jade Amulet",
                "implicit_mods": ["+25 to Dexterity"],
                "explicit_mods": [
                    "+100 to maximum Life",  # +20 improvement
                    "+45% to Fire Resistance",
                    "+32% to Cold Resistance",
                ],
            },
            {
                # Same life, better resistances
                "base_type": "Jade Amulet",
                "implicit_mods": ["+25 to Dexterity"],
                "explicit_mods": [
                    "+80 to maximum Life",
                    "+50% to Fire Resistance",  # +5 improvement
                    "+40% to Cold Resistance",  # +8 improvement
                ],
            },
            {
                # Slight downgrade in life, big resist improvement
                "base_type": "Jade Amulet",
                "implicit_mods": ["+25 to Dexterity"],
                "explicit_mods": [
                    "+70 to maximum Life",  # -10
                    "+50% to Fire Resistance",  # +5
                    "+50% to Cold Resistance",  # +18
                    "+15% to all Elemental Resistances",  # +15 to each
                ],
            },
        ]

        # Step 6: Rank upgrades
        prices = [25.0, 50.0, 75.0]
        ranked_upgrades = rank_upgrades(
            current_amulet,
            candidate_items,
            candidate_prices=prices,
        )

        # Step 7: Verify results
        assert len(ranked_upgrades) == 3

        # All should be upgrades (positive scores)
        for upgrade in ranked_upgrades:
            assert upgrade.score > 0, f"Expected upgrade, got score {upgrade.score}"

        # Results should be sorted by score (best first)
        assert ranked_upgrades[0].score >= ranked_upgrades[1].score
        assert ranked_upgrades[1].score >= ranked_upgrades[2].score

        # Verify best upgrade has improvements
        best_upgrade = ranked_upgrades[0]
        assert best_upgrade.improvements  # Should have some improvements
        assert best_upgrade.price_chaos in prices

        # Verify we can get summary
        summary = best_upgrade.get_summary()
        assert "Upgrade Score" in summary
        assert "chaos" in summary

    def test_no_upgrades_found(self):
        """Test flow when all candidates are downgrades."""
        # Parse build
        parsed_build = parse_pob_xml(SAMPLE_POB_XML, Game.POE1)
        current_amulet = parsed_build.items["Amulet"]

        # Create candidates that are all worse
        candidates = [
            {
                "base_type": "Jade Amulet",
                "explicit_mods": ["+50 to maximum Life"],  # -30 life
            },
            {
                "base_type": "Jade Amulet",
                "explicit_mods": ["+60 to maximum Life"],  # -20 life
            },
        ]

        # Rank upgrades
        results = rank_upgrades(current_amulet, candidates)

        # All should have negative scores (downgrades)
        assert all(r.score < 0 for r in results)

        # Still sorted by score (least bad first)
        assert results[0].score > results[1].score
