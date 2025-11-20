"""Tests for Trade API client.

These tests use mocked HTTP responses to avoid hitting the real Trade API.
This allows us to:
- Test without rate limiting concerns
- Test error handling
- Have fast, deterministic tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.contexts.upstream.services.trade_api_client import (
    search_items,
    fetch_items,
    search_and_fetch_items,
    build_simple_query,
)
from src.shared import Game


class TestBuildSimpleQuery:
    """Test query building function."""

    def test_minimal_query(self):
        """Test building query with just item type."""
        query = build_simple_query("Jade Amulet")

        assert query["query"]["type"] == "Jade Amulet"
        assert query["query"]["status"]["option"] == "online"
        assert query["sort"]["price"] == "asc"

    def test_query_with_life_filter(self):
        """Test building query with life requirement."""
        query = build_simple_query("Jade Amulet", min_life=60)

        assert query["query"]["type"] == "Jade Amulet"
        assert "stats" in query["query"]

        stats = query["query"]["stats"][0]
        assert stats["type"] == "and"
        assert len(stats["filters"]) == 1

        life_filter = stats["filters"][0]
        assert life_filter["id"] == "pseudo.pseudo_total_life"
        assert life_filter["value"]["min"] == 60

    def test_query_with_price_filter(self):
        """Test building query with max price."""
        query = build_simple_query("Jade Amulet", max_price_chaos=50)

        assert "trade_filters" in query["query"]["filters"]
        price_filter = query["query"]["filters"]["trade_filters"]["filters"]["price"]
        assert price_filter["max"] == 50

    def test_query_with_all_filters(self):
        """Test building query with all filters."""
        query = build_simple_query(
            "Jade Amulet",
            min_life=60,
            max_price_chaos=50,
            online_only=False,
        )

        assert query["query"]["type"] == "Jade Amulet"
        assert query["query"]["status"]["option"] == "any"  # Not online-only

        # Has life filter
        assert "stats" in query["query"]
        assert query["query"]["stats"][0]["filters"][0]["id"] == "pseudo.pseudo_total_life"

        # Has price filter
        assert "trade_filters" in query["query"]["filters"]


class TestSearchItems:
    """Test Trade API search functionality."""

    @pytest.mark.asyncio
    async def test_search_returns_result_ids(self):
        """Test that search returns list of result IDs."""
        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": ["abc123", "def456", "ghi789"],
            "total": 3,
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            query = build_simple_query("Jade Amulet")
            result_ids = await search_items(Game.POE1, "Standard", query)

            assert result_ids == ["abc123", "def456", "ghi789"]
            assert len(result_ids) == 3

            # Verify correct URL was called
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "Standard" in call_args[0][0]  # League in URL

    @pytest.mark.asyncio
    async def test_search_respects_limit(self):
        """Test that search limits results correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": ["id1", "id2", "id3", "id4", "id5"],
            "total": 5,
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            query = build_simple_query("Jade Amulet")
            result_ids = await search_items(Game.POE1, "Standard", query, limit=3)

            assert len(result_ids) == 3
            assert result_ids == ["id1", "id2", "id3"]

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self):
        """Test that search handles empty result set."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [],
            "total": 0,
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            query = build_simple_query("Jade Amulet")
            result_ids = await search_items(Game.POE1, "Standard", query)

            assert result_ids == []


class TestFetchItems:
    """Test Trade API fetch functionality."""

    @pytest.mark.asyncio
    async def test_fetch_returns_item_details(self):
        """Test that fetch returns full item details."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "id": "abc123",
                    "item": {
                        "name": "Corruption Choker",
                        "typeLine": "Jade Amulet",
                        "baseType": "Jade Amulet",
                    },
                    "listing": {
                        "price": {"amount": 25, "currency": "chaos"},
                    },
                }
            ]
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            items = await fetch_items(Game.POE1, ["abc123"])

            assert len(items) == 1
            assert items[0]["id"] == "abc123"
            assert items[0]["item"]["name"] == "Corruption Choker"

            # Verify correct URL was called
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "abc123" in call_args[0][0]  # ID in URL

    @pytest.mark.asyncio
    async def test_fetch_handles_empty_list(self):
        """Test that fetch handles empty ID list gracefully."""
        items = await fetch_items(Game.POE1, [])
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_limits_to_10_items(self):
        """Test that fetch limits to 10 items per request."""
        # Create 15 IDs
        result_ids = [f"id{i}" for i in range(15)]

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": []}

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await fetch_items(Game.POE1, result_ids)

            # Verify URL only contains first 10 IDs
            call_args = mock_client.get.call_args
            url = call_args[0][0]

            # Count commas (separator between IDs)
            comma_count = url.count(",")
            assert comma_count == 9  # 10 items = 9 commas


class TestSearchAndFetchItems:
    """Test combined search and fetch flow."""

    @pytest.mark.asyncio
    async def test_search_and_fetch_full_flow(self):
        """Test the complete search → fetch flow."""
        # Mock search response
        search_response = MagicMock()
        search_response.json.return_value = {
            "result": ["abc123", "def456"],
            "total": 2,
        }

        # Mock fetch response
        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "result": [
                {
                    "id": "abc123",
                    "item": {"name": "Item 1"},
                    "listing": {"price": {"amount": 10, "currency": "chaos"}},
                },
                {
                    "id": "def456",
                    "item": {"name": "Item 2"},
                    "listing": {"price": {"amount": 20, "currency": "chaos"}},
                },
            ]
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=search_response)
            mock_client.get = AsyncMock(return_value=fetch_response)
            mock_get_client.return_value = mock_client

            query = build_simple_query("Jade Amulet", min_life=60)
            items = await search_and_fetch_items(Game.POE1, "Standard", query, limit=10)

            assert len(items) == 2
            assert items[0]["item"]["name"] == "Item 1"
            assert items[1]["item"]["name"] == "Item 2"

            # Verify both search and fetch were called
            assert mock_client.post.call_count == 1
            assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_search_and_fetch_handles_no_results(self):
        """Test flow when search returns no results."""
        search_response = MagicMock()
        search_response.json.return_value = {
            "result": [],
            "total": 0,
        }

        with patch("src.contexts.upstream.services.trade_api_client.get_http_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=search_response)
            mock_client.get = AsyncMock()  # Should not be called
            mock_get_client.return_value = mock_client

            query = build_simple_query("Jade Amulet")
            items = await search_and_fetch_items(Game.POE1, "Standard", query)

            assert items == []

            # Verify fetch was NOT called (no results to fetch)
            mock_client.get.assert_not_called()
