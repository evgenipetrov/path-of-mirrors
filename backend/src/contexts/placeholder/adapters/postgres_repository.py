"""PostgreSQL adapter for Note repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import Game

from ..domain.models import Note
from ..ports.repository import NoteRepository


class PostgresNoteRepository(NoteRepository):
    """PostgreSQL implementation of NoteRepository.

    This adapter uses SQLAlchemy async sessions to persist notes
    to a PostgreSQL database.
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy async session.
        """
        self.db = db

    async def create(self, note: Note) -> Note:
        """Create a new note in the database.

        Args:
            note: Note to create.

        Returns:
            Note: Created note with generated ID and timestamps.
        """
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_by_id(self, note_id: UUID) -> Note | None:
        """Get a note by ID from the database.

        Args:
            note_id: Note ID.

        Returns:
            Note | None: Note if found, None otherwise.
        """
        result = await self.db.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    async def get_all(self, game: Game | None = None) -> list[Note]:
        """Get all notes from the database, optionally filtered by game.

        Args:
            game: Optional game filter (poe1 or poe2).

        Returns:
            list[Note]: List of notes.
        """
        query = select(Note)
        if game:
            query = query.where(Note.game_context == game)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, note: Note) -> Note:
        """Update an existing note in the database.

        Args:
            note: Note with updated fields.

        Returns:
            Note: Updated note.
        """
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def delete(self, note_id: UUID) -> bool:
        """Delete a note by ID from the database.

        Args:
            note_id: Note ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        note = await self.get_by_id(note_id)
        if note:
            await self.db.delete(note)
            await self.db.commit()
            return True
        return False
