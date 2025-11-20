"""Pydantic schemas for builds API endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from src.shared import Game


class BuildAnalysisRequest(BaseModel):
    """Request schema for build analysis endpoint."""

    session_id: str = Field(
        ...,
        description="Session ID from /builds/parse endpoint",
    )


class BuildAnalysisResponse(BaseModel):
    """Response schema for build analysis endpoint.

    Returns calculated stat weights and build priorities.
    """

    archetype: str = Field(
        ...,
        description="Detected build archetype (e.g., 'life_based', 'es_based')",
    )
    suggested_weights: dict[str, float] = Field(
        ...,
        description="Recommended stat weights for this build",
    )
    upgrade_priorities: dict[str, list[str]] = Field(
        ...,
        description="Recommended stats to prioritize for each item slot",
    )
    current_stats: dict[str, int | None] = Field(
        ...,
        description="Current character stats (life, ES, level, etc.)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "archetype": "life_based",
                "suggested_weights": {
                    "life": 2.0,
                    "fire_res": 0.8,
                    "movement_speed": 1.0,
                },
                "upgrade_priorities": {
                    "Amulet": ["life", "fire_res", "cold_res"],
                    "Ring 1": ["life", "fire_res", "cold_res"],
                },
                "current_stats": {
                    "life": 5000,
                    "energy_shield": None,
                    "level": 85,
                },
            }
        }
    )


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
    - Session ID for subsequent requests
    """

    # Session management
    session_id: str = Field(
        ...,
        description="Temporary session ID for this build (valid for 1 hour)",
    )

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
    derived_stats: dict | None = Field(
        default=None,
        description="Optional stats derived from headless PoB (EHP, resists, DPS, etc.)",
    )

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
