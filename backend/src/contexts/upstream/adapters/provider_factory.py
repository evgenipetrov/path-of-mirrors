"""Provider factory for game-specific data sources.

Epic 1.1: Simple factory with stub providers
Epic 1.2: Enhanced with HTTP client configuration
"""

from src.shared import Game

from ..ports import BaseProvider
from .poe1_provider import PoE1Provider
from .poe2_provider import PoE2Provider


def get_provider(game: Game) -> BaseProvider:
    """Return the appropriate provider for the given game.

    Factory pattern implementation that returns game-specific providers.
    Uses match statement for clear game-to-provider mapping.

    Args:
        game: Game enum (POE1 or POE2)

    Returns:
        Provider implementation for the specified game.
        Epic 1.1: Returns stub provider (PoE1Provider or PoE2Provider)
        Epic 1.2: Returns configured HTTP client-based provider

    Raises:
        ValueError: If game is not supported

    Example:
        >>> from shared import Game
        >>> provider = get_provider(Game.POE1)
        >>> provider.game
        <Game.POE1: 'poe1'>

    Design Notes:
        - Uses match statement (Python 3.10+) for clarity
        - Returns new instance each time (stateless providers)
        - Epic 1.2 may add caching or singleton pattern if needed
    """
    match game:
        case Game.POE1:
            return PoE1Provider()
        case Game.POE2:
            return PoE2Provider()
        case _:
            # This should never happen due to enum constraints,
            # but included for completeness
            raise ValueError(
                f"Unsupported game: {game}. "
                f"Supported games: {[g.value for g in Game]}"
            )
