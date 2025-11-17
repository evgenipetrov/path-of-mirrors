"""Application configuration using Pydantic settings."""

import os
from enum import Enum

from pydantic_settings import BaseSettings
from starlette.config import Config

current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_file_dir, "..", ".env")
config = Config(env_path)


class AppSettings(BaseSettings):
    """Application metadata settings."""

    APP_NAME: str = config("APP_NAME", default="Path of Mirrors")
    APP_DESCRIPTION: str | None = config("APP_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default="0.1.0")
    LICENSE_NAME: str | None = config("LICENSE_NAME", default="MIT")
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)


class PostgresSettings(BaseSettings):
    """PostgreSQL database settings."""

    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="localhost")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="pathofmirrors")
    POSTGRES_ASYNC_PREFIX: str = config("POSTGRES_ASYNC_PREFIX", default="postgresql+asyncpg://")
    POSTGRES_URI: str = f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


class RedisCacheSettings(BaseSettings):
    """Redis cache settings."""

    REDIS_CACHE_HOST: str = config("REDIS_CACHE_HOST", default="localhost")
    REDIS_CACHE_PORT: int = config("REDIS_CACHE_PORT", default=6379)
    REDIS_CACHE_URL: str = f"redis://{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}"


class RedisQueueSettings(BaseSettings):
    """Redis queue (ARQ) settings for background jobs."""

    REDIS_QUEUE_HOST: str = config("REDIS_QUEUE_HOST", default="localhost")
    REDIS_QUEUE_PORT: int = config("REDIS_QUEUE_PORT", default=6379)
    REDIS_QUEUE_URL: str = f"redis://{REDIS_QUEUE_HOST}:{REDIS_QUEUE_PORT}"


class EnvironmentOption(Enum):
    """Deployment environment options."""

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    """Environment and logging settings."""

    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default=EnvironmentOption.LOCAL)
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")


class Settings(
    AppSettings,
    PostgresSettings,
    RedisCacheSettings,
    RedisQueueSettings,
    EnvironmentSettings,
):
    """Combined application settings."""

    pass


settings = Settings()
