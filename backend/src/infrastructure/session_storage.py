"""Redis-based session storage for temporary build data.

This module provides session management for storing parsed builds temporarily
without requiring database persistence. Sessions expire after 1 hour.

Use Cases:
- Store parsed PoB builds between parse and analyze steps
- Maintain build state during upgrade search flow
- Avoid re-parsing PoB code on every request
"""

import json
from typing import Any, cast
from uuid import uuid4

import structlog

from src.infrastructure.cache import get_cache

logger = structlog.get_logger(__name__)

# Session configuration
SESSION_PREFIX = "build_session:"
SESSION_TTL = 3600  # 1 hour in seconds


async def create_session(data: dict[str, Any]) -> str:
    """Create a new session and store data.

    Args:
        data: Dictionary to store in session (will be JSON serialized)

    Returns:
        Session ID (UUID)

    Example:
        >>> session_id = await create_session({"build": {...}, "timestamp": ...})
        >>> print(session_id)
        "550e8400-e29b-41d4-a716-446655440000"
    """
    session_id = str(uuid4())
    cache = await get_cache()

    # Serialize to JSON
    serialized = json.dumps(data)

    # Store in Redis with TTL
    key = f"{SESSION_PREFIX}{session_id}"
    await cache.setex(key, SESSION_TTL, serialized)

    logger.info(
        "Session created",
        session_id=session_id,
        ttl=SESSION_TTL,
        data_size=len(serialized),
    )

    return session_id


async def get_session(session_id: str) -> dict[str, Any] | None:
    """Retrieve session data by ID.

    Args:
        session_id: Session ID to retrieve

    Returns:
        Session data dict or None if not found/expired

    Example:
        >>> data = await get_session("550e8400-...")
        >>> print(data["build"]["name"])
        "RF Juggernaut"
    """
    cache = await get_cache()
    key = f"{SESSION_PREFIX}{session_id}"

    # Get from Redis
    serialized = await cache.get(key)

    if serialized is None:
        logger.warning("Session not found", session_id=session_id)
        return None

    # Deserialize
    data = cast(dict[str, Any], json.loads(serialized))

    logger.debug("Session retrieved", session_id=session_id)

    return data


async def update_session(session_id: str, data: dict[str, Any]) -> bool:
    """Update existing session data.

    Args:
        session_id: Session ID to update
        data: New data to store (replaces existing)

    Returns:
        True if updated, False if session not found

    Example:
        >>> updated = await update_session("550e8400-...", {"build": {...}, "weights": {...}})
        >>> assert updated is True
    """
    cache = await get_cache()
    key = f"{SESSION_PREFIX}{session_id}"

    # Check if exists
    exists = await cache.exists(key)
    if not exists:
        logger.warning("Cannot update - session not found", session_id=session_id)
        return False

    # Update with same TTL
    serialized = json.dumps(data)
    await cache.setex(key, SESSION_TTL, serialized)

    logger.info("Session updated", session_id=session_id)

    return True


async def delete_session(session_id: str) -> bool:
    """Delete a session.

    Args:
        session_id: Session ID to delete

    Returns:
        True if deleted, False if not found

    Example:
        >>> deleted = await delete_session("550e8400-...")
        >>> assert deleted is True
    """
    cache = await get_cache()
    key = f"{SESSION_PREFIX}{session_id}"

    deleted = await cache.delete(key)

    if deleted:
        logger.info("Session deleted", session_id=session_id)
    else:
        logger.warning("Session not found for deletion", session_id=session_id)

    return bool(deleted)


async def extend_session(session_id: str) -> bool:
    """Extend session TTL by another hour.

    Useful when user is actively working with a build.

    Args:
        session_id: Session ID to extend

    Returns:
        True if extended, False if not found

    Example:
        >>> extended = await extend_session("550e8400-...")
        >>> assert extended is True
    """
    cache = await get_cache()
    key = f"{SESSION_PREFIX}{session_id}"

    # Expire extends TTL, returns 1 if key exists
    extended = await cache.expire(key, SESSION_TTL)

    if extended:
        logger.info("Session TTL extended", session_id=session_id, new_ttl=SESSION_TTL)
    else:
        logger.warning("Cannot extend - session not found", session_id=session_id)

    return bool(extended)
