"""Shared HTTP client for all upstream API calls.

This module provides a centralized HTTP client for communicating with external
APIs like Trade API, poe.ninja, etc.

Key Features:
- User-Agent compliance (required by PoE APIs)
- Consistent error handling
- Future: Rate limiting support
- Future: Retry logic with exponential backoff
"""

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class UpstreamHttpClient:
    """Shared HTTP client for upstream API calls.

    This client wraps httpx.AsyncClient with:
    - Required User-Agent headers
    - Consistent error handling
    - Logging for debugging

    Example:
        >>> client = UpstreamHttpClient()
        >>> async with client.session() as session:
        ...     response = await session.get("https://api.example.com")
    """

    def __init__(
        self,
        user_agent: str = "PathOfMirrors/1.0 (contact: your-email@example.com)",
        timeout: float = 30.0,
    ):
        """Initialize the HTTP client.

        Args:
            user_agent: User-Agent header (required by PoE APIs)
            timeout: Default timeout in seconds for all requests
        """
        self.user_agent = user_agent
        self.timeout = timeout

        # Default headers for all requests
        self.default_headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
        }

    def session(self) -> httpx.AsyncClient:
        """Create an async HTTP session with default configuration.

        Returns:
            Configured httpx.AsyncClient

        Example:
            >>> async with client.session() as session:
            ...     response = await session.get(url)
        """
        return httpx.AsyncClient(
            headers=self.default_headers,
            timeout=self.timeout,
            follow_redirects=True,
        )

    async def get(
        self, url: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform GET request with error handling.

        Args:
            url: URL to request
            params: Query parameters
            **kwargs: Additional arguments passed to httpx

        Returns:
            Response object

        Raises:
            httpx.HTTPStatusError: For 4xx/5xx responses
            httpx.TimeoutException: For timeout errors

        Example:
            >>> response = await client.get("https://api.example.com", params={"q": "test"})
        """
        async with self.session() as session:
            logger.debug("GET request", url=url, params=params)

            try:
                response = await session.get(url, params=params, **kwargs)
                response.raise_for_status()

                logger.debug(
                    "GET response",
                    url=url,
                    status_code=response.status_code,
                    content_length=len(response.content),
                )

                return response

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "HTTP error",
                    url=url,
                    status_code=e.response.status_code,
                    error=str(e),
                )
                raise

            except httpx.TimeoutException:
                logger.error("Request timeout", url=url, timeout=self.timeout)
                raise

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform POST request with error handling.

        Args:
            url: URL to request
            json: JSON body (if any)
            data: Form data (if any)
            **kwargs: Additional arguments passed to httpx

        Returns:
            Response object

        Raises:
            httpx.HTTPStatusError: For 4xx/5xx responses
            httpx.TimeoutException: For timeout errors

        Example:
            >>> response = await client.post("https://api.example.com", json={"key": "value"})
        """
        async with self.session() as session:
            logger.debug(
                "POST request",
                url=url,
                has_json=json is not None,
                has_data=data is not None,
            )

            try:
                response = await session.post(url, json=json, data=data, **kwargs)
                response.raise_for_status()

                logger.debug(
                    "POST response",
                    url=url,
                    status_code=response.status_code,
                    content_length=len(response.content),
                )

                return response

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "HTTP error",
                    url=url,
                    status_code=e.response.status_code,
                    error=str(e),
                    response_body=e.response.text[:200] if e.response.text else None,
                )
                raise

            except httpx.TimeoutException:
                logger.error("Request timeout", url=url, timeout=self.timeout)
                raise


# Global singleton instance
# Can be configured via environment variables in production
_default_client: UpstreamHttpClient | None = None


def get_http_client() -> UpstreamHttpClient:
    """Get the default HTTP client instance.

    Returns:
        Shared UpstreamHttpClient instance

    Example:
        >>> client = get_http_client()
        >>> response = await client.get("https://api.example.com")
    """
    global _default_client
    if _default_client is None:
        _default_client = UpstreamHttpClient()
    return _default_client
