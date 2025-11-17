"""Health check utilities for database and Redis."""

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .logging import get_logger

logger = get_logger(__name__)


async def check_database_health(db: AsyncSession) -> bool:
    """Check if database is healthy by executing a simple query.

    Args:
        db: Database session.

    Returns:
        bool: True if database is healthy, False otherwise.
    """
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


async def check_redis_health(redis: Redis) -> bool:
    """Check if Redis is healthy by sending a PING command.

    Args:
        redis: Redis client.

    Returns:
        bool: True if Redis is healthy, False otherwise.
    """
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return False
