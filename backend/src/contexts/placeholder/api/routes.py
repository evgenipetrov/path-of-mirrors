"""FastAPI routes for Note CRUD operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure import get_db
from shared import Game

from ..adapters.postgres_repository import PostgresNoteRepository
from ..domain.schemas import NoteCreate, NoteResponse, NoteUpdate
from ..services.note_service import NoteService

router = APIRouter(prefix="/api/notes", tags=["notes"])


def get_note_service(db: AsyncSession = Depends(get_db)) -> NoteService:
    """Dependency for getting NoteService.

    Args:
        db: Database session.

    Returns:
        NoteService: Initialized note service.
    """
    repository = PostgresNoteRepository(db)
    return NoteService(repository)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
)
async def create_note(
    note_data: NoteCreate,
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """Create a new note.

    Args:
        note_data: Note creation data.
        service: Note service dependency.

    Returns:
        NoteResponse: Created note.
    """
    note = await service.create_note(note_data)
    return NoteResponse.model_validate(note)


@router.get(
    "",
    response_model=list[NoteResponse],
    summary="List all notes",
)
async def list_notes(
    game: Game | None = Query(None, description="Filter by game (poe1 or poe2)"),
    service: NoteService = Depends(get_note_service),
) -> list[NoteResponse]:
    """List all notes, optionally filtered by game.

    Args:
        game: Optional game filter.
        service: Note service dependency.

    Returns:
        list[NoteResponse]: List of notes.
    """
    notes = await service.list_notes(game)
    return [NoteResponse.model_validate(note) for note in notes]


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
)
async def get_note(
    note_id: UUID,
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """Get a note by ID.

    Args:
        note_id: Note ID.
        service: Note service dependency.

    Returns:
        NoteResponse: Note.

    Raises:
        HTTPException: 404 if note not found.
    """
    note = await service.get_note(note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
    return NoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
)
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    """Update an existing note.

    Args:
        note_id: Note ID.
        note_data: Note update data.
        service: Note service dependency.

    Returns:
        NoteResponse: Updated note.

    Raises:
        HTTPException: 404 if note not found.
    """
    note = await service.update_note(note_id, note_data)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
)
async def delete_note(
    note_id: UUID,
    service: NoteService = Depends(get_note_service),
) -> None:
    """Delete a note.

    Args:
        note_id: Note ID.
        service: Note service dependency.

    Raises:
        HTTPException: 404 if note not found.
    """
    deleted = await service.delete_note(note_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found",
        )
