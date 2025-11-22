"""Tests for HTTP client lifecycle management."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app, get_http_client


def test_http_client_initialized_after_startup() -> None:
    """Test that HTTP client is initialized during app startup."""
    with TestClient(app):
        # After entering the context, the app should be started and client initialized
        http_client = get_http_client()
        assert http_client is not None
        assert not http_client.is_closed


def test_http_client_configured_correctly() -> None:
    """Test that HTTP client has correct configuration."""
    with TestClient(app):
        http_client = get_http_client()

        # Check headers are set
        assert "User-Agent" in http_client.headers
        assert "Accept" in http_client.headers
        assert http_client.headers["Accept"] == "application/json"

        # Check timeout is configured
        assert http_client.timeout.read == 30.0

        # Check redirect following is enabled
        assert http_client.follow_redirects is True


@pytest.mark.asyncio
async def test_http_client_closes_on_shutdown() -> None:
    """Test that HTTP client aclose() is called during app shutdown."""
    from unittest.mock import AsyncMock

    import src.main

    # Create a mock client that we can verify gets closed
    mock_client = MagicMock()
    mock_client.aclose = AsyncMock()  # aclose is async, needs AsyncMock

    # Patch httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Start the app (which creates the client in lifespan)
        with TestClient(app):
            # Verify the client is our mock
            assert src.main._http_client is mock_client

        # After exiting the context, aclose should have been called
        mock_client.aclose.assert_called_once()


def test_get_http_client_raises_before_initialization() -> None:
    """Test that get_http_client raises RuntimeError when called before app startup."""
    import src.main

    # Save the current client
    original_client = src.main._http_client

    try:
        # Set client to None to simulate before-startup state
        src.main._http_client = None

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="HTTP client not initialized"):
            get_http_client()
    finally:
        # Restore original client
        src.main._http_client = original_client
