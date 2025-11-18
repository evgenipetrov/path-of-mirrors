"""Repository port (interface) for Note operations."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.shared import Game

from ..domain.models import Note


class NoteRepository(ABC):
    """Abstract repository for Note CRUD operations.

    This port defines the interface that adapters must implement.
    It isolates the domain logic from infrastructure concerns.
    """

    @abstractmethod
    async def create(self, note: Note) -> Note:
        """Create a new note.

        Args:
            note: Note to create.

        Returns:
            Note: Created note with generated ID and timestamps.
        """
        pass

    @abstractmethod
    async def get_by_id(self, note_id: UUID) -> Note | None:
        """Get a note by ID.

        Args:
            note_id: Note ID.

        Returns:
            Note | None: Note if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all(self, game: Game | None = None) -> list[Note]:
        """Get all notes, optionally filtered by game.

        Args:
            game: Optional game filter (poe1 or poe2).

        Returns:
            list[Note]: List of notes.
        """
        pass

    @abstractmethod
    async def update(self, note: Note) -> Note:
        """Update an existing note.

        Args:
            note: Note with updated fields.

        Returns:
            Note: Updated note.
        """
        pass

    @abstractmethod
    async def delete(self, note_id: UUID) -> bool:
        """Delete a note by ID.

        Args:
            note_id: Note ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        pass
