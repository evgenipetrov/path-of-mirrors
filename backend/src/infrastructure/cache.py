"""Redis cache client."""

import redis.asyncio as redis
from redis.asyncio.client import Redis

from .settings import settings

# Create Redis client for caching
redis_client: Redis = redis.from_url(
    settings.REDIS_CACHE_URL,
    decode_responses=True,
)


async def get_cache() -> Redis:
    """Get Redis cache client.

    Returns:
        redis.Redis: Redis client instance.
    """
    return redis_client


async def close_cache() -> None:
    """Close Redis cache connection."""
    await redis_client.close()
