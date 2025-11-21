"""Shared HTTP utilities for external API calls."""

import httpx
import structlog

logger = structlog.get_logger(__name__)


def create_poe_http_client(
    user_agent: str = "PathOfMirrors/1.0 (contact: your-email@example.com)",
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    """Create an HTTP client configured for PoE API calls.

    Returns a configured httpx.AsyncClient with:
    - Required User-Agent headers
    - JSON accept header
    - Timeout configuration
    - Redirect following
    """
    return httpx.AsyncClient(
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        timeout=timeout,
        follow_redirects=True,
    )
