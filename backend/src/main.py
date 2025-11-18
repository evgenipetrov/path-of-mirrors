"""Path of Mirrors - FastAPI Application Entry Point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from contexts.placeholder.api.routes import router as notes_router
from infrastructure import (
    RequestLoggingMiddleware,
    check_database_health,
    check_redis_health,
    close_cache,
    get_cache,
    get_db,
    get_logger,
    settings,
    setup_logging,
)

# Setup structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control flow during application lifetime.
    """
    # Startup
    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT.value,
        app_name=settings.APP_NAME,
    )

    yield

    # Shutdown
    logger.info("application_shutdown")
    await close_cache()


# Create FastAPI application
contact_info = {
    key: value
    for key, value in {
        "name": settings.CONTACT_NAME,
        "email": settings.CONTACT_EMAIL,
    }.items()
    if value
}

license_info = {"name": settings.LICENSE_NAME} if settings.LICENSE_NAME else None

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION or "Path of Mirrors API",
    version=settings.APP_VERSION or "0.1.0",
    contact=contact_info or None,
    license_info=license_info,
    lifespan=lifespan,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS (permissive for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT.value == "local" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notes_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Basic liveness check endpoint.

    This endpoint always returns 200 OK if the application is running.
    Use /ready for readiness checks that verify dependencies.

    Returns:
        dict[str, str]: Health status.
    """
    return {"status": "healthy"}


@app.get("/ready", tags=["health"])
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Readiness check endpoint that verifies database and Redis connectivity.

    Returns 200 if all dependencies are healthy, 503 otherwise.

    Args:
        db: Database session dependency.

    Returns:
        dict: Readiness status with individual component health.
    """
    # Check database
    db_healthy = await check_database_health(db)

    # Check Redis
    redis = await get_cache()
    redis_healthy = await check_redis_health(redis)

    # Overall readiness
    is_ready = db_healthy and redis_healthy

    # Log if not ready
    if not is_ready:
        logger.warning(
            "readiness_check_failed",
            database_healthy=db_healthy,
            redis_healthy=redis_healthy,
        )

    # Return appropriate status code
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    response = {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "database": db_healthy,
            "redis": redis_healthy,
        },
    }

    # FastAPI will use the status code from Response if we return one
    # For now, we'll handle this in a simpler way
    return JSONResponse(content=response, status_code=status_code)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
