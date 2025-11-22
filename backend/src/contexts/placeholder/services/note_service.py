"""Service layer for Note operations."""

from uuid import UUID

from src.infrastructure import get_logger
from src.shared import Game

from ..domain.models import Note
from ..domain.schemas import NoteCreate, NoteUpdate
from ..ports.repository import NoteRepository

logger = get_logger(__name__)


class NoteService:
    """Service for business logic related to notes.

    This service orchestrates repository operations and contains
    domain logic that doesn't belong in the repository or API layers.
    """

    def __init__(self, repository: NoteRepository):
        """Initialize service with repository.

        Args:
            repository: Note repository implementation.
        """
        self.repository = repository

    async def create_note(self, note_data: NoteCreate, game: Game) -> Note:
        """Create a new note.

        Args:
            note_data: Note creation data.
            game: Game context from path parameter.

        Returns:
            Note: Created note.
        """
        note = Note(
            title=note_data.title,
            content=note_data.content,
            game_context=game,
        )
        created_note = await self.repository.create(note)
        logger.info(
            "note_created",
            note_id=str(created_note.id),
            game_context=created_note.game_context,
        )
        return created_note

    async def get_note(self, note_id: UUID) -> Note | None:
        """Get a note by ID.

        Args:
            note_id: Note ID.

        Returns:
            Note | None: Note if found, None otherwise.
        """
        return await self.repository.get_by_id(note_id)

    async def list_notes(self, game: Game | None = None) -> list[Note]:
        """List all notes, optionally filtered by game.

        Args:
            game: Optional game filter.

        Returns:
            list[Note]: List of notes.
        """
        return await self.repository.get_all(game)

    async def update_note(
        self, note_id: UUID, note_data: NoteUpdate, game: Game | None = None
    ) -> Note | None:
        """Update an existing note.

        Args:
            note_id: Note ID.
            note_data: Note update data.
            game: Optional game context from path parameter (for validation).

        Returns:
            Note | None: Updated note if found, None otherwise.
        """
        note = await self.repository.get_by_id(note_id)
        if not note:
            return None

        # Validate game context if provided
        if game is not None and note.game_context != game:
            return None

        # Update only fields that were explicitly provided in the request
        # This allows setting fields to None explicitly
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        updated_note = await self.repository.update(note)
        logger.info(
            "note_updated",
            note_id=str(updated_note.id),
            game_context=updated_note.game_context,
        )
        return updated_note

    async def delete_note(self, note_id: UUID) -> bool:
        """Delete a note.

        Args:
            note_id: Note ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        deleted = await self.repository.delete(note_id)
        if deleted:
            logger.info("note_deleted", note_id=str(note_id))
        return deleted
