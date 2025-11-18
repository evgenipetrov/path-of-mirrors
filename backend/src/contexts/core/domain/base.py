"""Base domain models and mixins for all contexts.

This module provides the foundational building blocks for domain entities:
- TimestampMixin: Automatic created_at/updated_at tracking
- UUIDPrimaryKeyMixin: Standard UUID primary key
- BaseEntity: Abstract base combining both mixins

All domain entities should extend BaseEntity for consistency.
"""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from src.infrastructure import Base


class TimestampMixin(MappedAsDataclass):
    """Mixin for entities that track creation and update times.

    Provides automatic timestamp management for domain entities.
    Uses database-level defaults for consistency across contexts.
    """

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        init=False,
        doc="Timestamp when entity was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
        doc="Timestamp when entity was last updated",
    )


class UUIDPrimaryKeyMixin(MappedAsDataclass):
    """Mixin for entities using UUID as primary key.

    Uses UUID v4 for globally unique identifiers.
    The `init=False` ensures SQLAlchemy generates the ID automatically.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        insert_default=uuid4,
        init=False,
        doc="Unique identifier for this entity",
    )


class BaseEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Abstract base class for all domain entities.

    Provides:
    - UUID primary key
    - Automatic timestamp tracking (created_at, updated_at)
    - Common metadata fields

    Usage:
        class MyEntity(BaseEntity):
            __tablename__ = "my_entities"

            name: Mapped[str]
            game_context: Mapped[Game]
    """

    __abstract__ = True

    # Type annotation for SQLAlchemy table name
    __tablename__: ClassVar[str]

    def __repr__(self) -> str:
        """String representation showing entity type and ID."""
        return f"<{self.__class__.__name__}(id={self.id})>"
