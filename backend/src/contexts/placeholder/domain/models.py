"""Domain models for the placeholder context."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure import Base
from shared import Game


class Note(Base):
    """A simple note entity for testing the stack.

    This is a placeholder CRUD entity used to validate the full-stack setup
    before implementing real Path of Mirrors features.
    """

    __tablename__ = "notes"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid4, init=False)

    # Fields (required fields must come before optional fields for dataclass)
    title: Mapped[str] = mapped_column(String(255))
    game_context: Mapped[Game] = mapped_column(String(10))
    content: Mapped[str | None] = mapped_column(Text, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )

    def __repr__(self) -> str:
        """String representation of the Note."""
        return f"<Note(id={self.id}, title='{self.title}', game={self.game_context})>"
