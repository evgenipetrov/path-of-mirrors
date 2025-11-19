"""Pydantic schemas for upstream API endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from src.shared import Game


class PoBParseRequest(BaseModel):
    """Request schema for PoB parsing endpoint.

    Accepts either:
    - pob_xml: Raw XML string from .xml file
    - pob_code: Base64+zlib import code (the long string users paste)

    One of these fields must be provided.
    """

    pob_xml: str | None = Field(
        None,
        description="Raw Path of Building XML content",
        min_length=1,
    )
    pob_code: str | None = Field(
        None,
        description="Path of Building import code (base64 encoded)",
        min_length=1,
    )
    game: Game = Field(
        ...,
        description="Game context (poe1 or poe2)",
    )


class PoBParseResponse(BaseModel):
    """Response schema for PoB parsing endpoint.

    Returns a standardized Build representation with:
    - Character info (class, level, ascendancy)
    - Items (slot-mapped equipment)
    - Build metadata (name, source)
    """

    # Character info
    game: Game
    name: str
    character_class: str
    level: int
    ascendancy: str | None = None
    league: str | None = None

    # Character stats (optional)
    life: int | None = None
    energy_shield: int | None = None
    mana: int | None = None
    armour: int | None = None
    evasion: int | None = None

    # Build components
    items: dict | None = None  # Slot-mapped items
    passive_tree: dict | None = None
    skills: list[dict] | None = None

    # Metadata
    source: str = "pob"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "game": "poe1",
                "name": "RF Juggernaut",
                "character_class": "Marauder",
                "level": 95,
                "ascendancy": "Juggernaut",
                "items": {
                    "Weapon 1": {
                        "name": "The Dark Seer",
                        "base_type": "Shadow Sceptre",
                        "rarity": "UNIQUE",
                    }
                },
                "source": "pob",
            }
        }
    )
