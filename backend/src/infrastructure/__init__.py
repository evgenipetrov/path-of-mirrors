"""Infrastructure layer - cross-cutting concerns."""

from .cache import close_cache, get_cache, redis_client
from .config import (
    GlobalConfig,
    PoBConfig,
    PoeDBConfig,
    PoeNinjaConfig,
    TradeConfig,
    get_global_config,
    get_pob_config,
    get_poedb_config,
    get_poeninja_config,
    get_trade_config,
)
from .database import Base, async_engine, get_db, local_session
from .health import check_database_health, check_redis_health
from .logging import get_logger, setup_logging
from .middleware import RequestLoggingMiddleware
from .session_storage import (
    create_session,
    delete_session,
    extend_session,
    get_session,
    update_session,
)
from .settings import settings

__all__ = [
    # Config (app-level)
    "settings",
    # Config (upstream sources - global)
    "GlobalConfig",
    "get_global_config",
    # Config (upstream sources - poe.ninja)
    "PoeNinjaConfig",
    "get_poeninja_config",
    # Config (upstream sources - Trade API)
    "TradeConfig",
    "get_trade_config",
    # Config (upstream sources - PoeDB)
    "PoeDBConfig",
    "get_poedb_config",
    # Config (upstream sources - Path of Building)
    "PoBConfig",
    "get_pob_config",
    # Database
    "Base",
    "get_db",
    "async_engine",
    "local_session",
    # Cache
    "redis_client",
    "get_cache",
    "close_cache",
    # Session Storage
    "create_session",
    "get_session",
    "update_session",
    "delete_session",
    "extend_session",
    # Health
    "check_database_health",
    "check_redis_health",
    # Logging
    "setup_logging",
    "get_logger",
    # Middleware
    "RequestLoggingMiddleware",
]
