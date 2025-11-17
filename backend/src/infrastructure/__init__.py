"""Infrastructure layer - cross-cutting concerns."""

from .cache import close_cache, get_cache, redis_client
from .config import settings
from .database import Base, async_engine, get_db, local_session
from .health import check_database_health, check_redis_health
from .logging import get_logger, setup_logging
from .middleware import RequestLoggingMiddleware

__all__ = [
    # Config
    "settings",
    # Database
    "Base",
    "get_db",
    "async_engine",
    "local_session",
    # Cache
    "redis_client",
    "get_cache",
    "close_cache",
    # Health
    "check_database_health",
    "check_redis_health",
    # Logging
    "setup_logging",
    "get_logger",
    # Middleware
    "RequestLoggingMiddleware",
]
