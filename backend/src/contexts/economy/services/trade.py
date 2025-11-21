"""Economy facade for PoE trade lookups, delegating to the upstream client."""

from typing import Any, cast

from src.contexts.upstream.services import trade_api_client as upstream_trade
from src.shared import Game

__all__ = [
    "build_simple_query",
    "search_items",
    "fetch_items",
    "search_and_fetch_items",
]


def build_simple_query(
    item_type: str,
    min_life: int | None = None,
    max_price_chaos: int | None = None,
    online_only: bool = True,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        upstream_trade.build_simple_query(
            item_type=item_type,
            min_life=min_life,
            max_price_chaos=max_price_chaos,
            online_only=online_only,
        ),
    )


async def search_items(
    game: Game,
    league: str,
    query: dict[str, Any],
    limit: int = 10,
) -> list[str]:
    return cast(
        list[str],
        await upstream_trade.search_items(
            game=game,
            league=league,
            query=query,
            limit=limit,
        ),
    )


async def fetch_items(
    game: Game,
    result_ids: list[str],
    query_id: str | None = None,
) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        await upstream_trade.fetch_items(
            game=game,
            result_ids=result_ids,
            query_id=query_id,
        ),
    )


async def search_and_fetch_items(
    game: Game,
    league: str,
    query: dict[str, Any],
    limit: int = 10,
) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        await upstream_trade.search_and_fetch_items(
            game=game,
            league=league,
            query=query,
            limit=limit,
        ),
    )
