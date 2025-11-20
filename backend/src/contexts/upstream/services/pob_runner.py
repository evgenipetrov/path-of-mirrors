"""Headless Path of Building runner (stub with graceful fallback).

This module is the integration point for invoking the Path of Building
Community Fork binaries (PoE1) and the PoE2 fork via a Lua bridge. For now it
is a thin shim that:
  - Reads configured binary paths from env (POB_CLI_POE1 / POB_CLI_POE2)
  - If binaries are absent, returns {} so callers can fall back to lightweight
    parsing.
  - Is structured so we can later swap in the real Lua bridge logic from
    `_samples/code/path-of-mirrors_v0.4`.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

from src.shared import Game
import structlog

logger = structlog.get_logger(__name__)


def _binary_for_game(game: Game) -> str | None:
    if game == Game.POE1:
        return os.getenv("POB_CLI_POE1")
    if game == Game.POE2:
        return os.getenv("POB_CLI_POE2")
    return None


def run_pob(xml_content: str, game: Game, timeout: int = 10) -> dict[str, Any]:
    """Invoke PoB headless CLI (if configured) to derive stats.

    Currently returns {} when the binary is not configured or invocation fails.
    This keeps upstream flows non-blocking while we wire in the real bridge.
    """
    binary = _binary_for_game(game)
    if not binary:
        logger.warn("pob_cli_not_configured", game=game.value)
        return {}

    try:
        result = subprocess.run(
            [binary, "--stdin"],  # placeholder interface
            input=xml_content.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("pob_cli_failed_launch", game=game.value, error=str(exc))
        return {}

    if result.returncode != 0:
        logger.warn(
            "pob_cli_nonzero_exit",
            game=game.value,
            code=result.returncode,
            stderr=result.stderr.decode("utf-8", errors="ignore")[:500],
        )
        return {}

    # Future: parse structured JSON from stdout; for now, return empty to avoid
    # blocking callers. Keep placeholder for quick swap-in.
    logger.info("pob_cli_called", game=game.value)
    return {}
