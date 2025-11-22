"""Data ingestion service for upstream sources (poe.ninja, trade API).

This module will handle scheduled data ingestion from external sources.

Planned scope:
- Fetch data from poe.ninja API (economies, leagues, item prices)
- Store snapshots in PostgreSQL with JSONB
- Cache normalized data in Redis
- Schedule periodic updates (requires background job system)

Status: Not yet implemented (placeholder for Phase 1)
"""


def ingest_economy_snapshot(game: str, league: str) -> None:
    """Fetch and store an economy snapshot from poe.ninja.

    Args:
        game: Game context ('poe1' or 'poe2')
        league: League name (e.g., 'Settlers', 'Standard')

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError(
        "Data ingestion is not yet implemented. "
        "Requires background job system (ARQ or alternative) and poe.ninja adapter integration."
    )
