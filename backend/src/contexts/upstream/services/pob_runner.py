"""Headless Path of Building runner with Lua bridge.

This integrates the Path of Building Community binaries (PoE1 + PoE2) via a
Lua bridge script executed under LuaJIT. It streams PoB build XML on stdin and
expects JSON on stdout.

Environment (defaults can be set in Docker image):
  POB_CLI_POE1: path to "Path of Building.exe" for PoE1
  POB_CLI_POE2: path to "Path of Building-PoE2.exe" for PoE2
  POB_LUAJIT:   path to luajit binary
  POB_BRIDGE:   path to pob_bridge.lua

Behavior:
  - If any prerequisite is missing, returns an empty dict (callers fall back to
    lightweight parsing rather than failing the request).
  - On success, returns parsed JSON emitted by the Lua bridge.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from typing import Any

import structlog

from src.shared import Game

logger = structlog.get_logger(__name__)


def _binary_for_game(game: Game) -> str | None:
    if game == Game.POE1:
        return os.getenv("POB_CLI_POE1")
    if game == Game.POE2:
        return os.getenv("POB_CLI_POE2")
    return None


def _is_executable(path: str | None) -> bool:
    if not path:
        return False
    return os.path.isfile(path) and os.access(path, os.X_OK)


def _missing_fields(items: Iterable[tuple[str, str | None]]) -> list[str]:
    return [name for name, value in items if not value]


def run_pob(xml_content: str, game: Game, timeout: int = 15) -> dict[str, Any]:
    """Invoke PoB via Lua bridge and parse JSON output.

    Returns {} if tooling is missing or invocation fails; callers should treat
    this as a graceful no-op and continue with fallback parsing.
    """

    pob_binary = _binary_for_game(game)
    luajit = os.getenv("POB_LUAJIT")
    bridge = os.getenv("POB_BRIDGE")

    missing = _missing_fields(
        [
            ("pob_binary", pob_binary),
            ("luajit", luajit),
            ("bridge", bridge),
        ]
    )
    if missing:
        logger.warn("pob_cli_missing_config", game=game.value, missing=missing)
        return {}

    if not _is_executable(luajit):
        logger.warn("luajit_not_executable", path=luajit)
        return {}

    # PoB binaries are Windows executables; we only validate that the path exists.
    if not pob_binary or not os.path.isfile(pob_binary):
        logger.warn("pob_binary_missing", game=game.value, path=pob_binary)
        return {}

    if not bridge or not os.path.isfile(bridge):
        logger.warn("pob_bridge_missing", path=bridge)
        return {}

    # At this point, values are non-None strings
    assert luajit is not None
    assert bridge is not None
    assert pob_binary is not None

    cmd: list[str] = [luajit, bridge, pob_binary]
    try:
        result = subprocess.run(
            cmd,
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

    stdout = result.stdout.decode("utf-8", errors="ignore")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        logger.warn("pob_cli_bad_json", sample=stdout[:200])
        return {}

    logger.info("pob_cli_ok", game=game.value)
    return payload if isinstance(payload, dict) else {}
