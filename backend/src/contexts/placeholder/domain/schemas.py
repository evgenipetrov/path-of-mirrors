"""Pydantic schemas for Note API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared import Game


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str | None = Field(None, description="Note content")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""

    title: str | None = Field(None, min_length=1, max_length=255, description="Note title")
    content: str | None = Field(None, description="Note content")


class NoteResponse(BaseModel):
    """Schema for note responses."""

    id: UUID
    title: str
    content: str | None
    game_context: Game
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
