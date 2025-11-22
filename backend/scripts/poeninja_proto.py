"""Protobuf decoding helpers for poe.ninja build search payloads.

This is a simplified version of the protobuf decoder used in the main codebase,
specifically for sample collection purposes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "BuildSummary",
    "BuildSearchData",
    "parse_build_search_payload",
]

# Protobuf wire types
_WIRE_VARINT = 0
_WIRE_64BIT = 1
_WIRE_LENGTH_DELIMITED = 2
_WIRE_START_GROUP = 3
_WIRE_END_GROUP = 4
_WIRE_32BIT = 5


@dataclass(frozen=True)
class BuildSummary:
    """Summary of a character build from poe.ninja ladder."""

    account: str
    character: str


@dataclass(frozen=True)
class BuildSearchData:
    """Parsed build search response."""

    summaries: list[BuildSummary]


def parse_build_search_payload(payload: bytes) -> BuildSearchData:
    """Parse protobuf-encoded build search response.

    Args:
        payload: Raw protobuf bytes from poe.ninja API

    Returns:
        BuildSearchData with list of build summaries
    """
    message = _parse_message(payload)
    if not message:
        return BuildSearchData([])

    root = message.get(1)
    if not root or not isinstance(root, list):
        return BuildSearchData([])

    container = root[0]
    # Container should be a dict (parsed nested message)
    if not isinstance(container, dict):
        return BuildSearchData([])

    summaries = _parse_summaries(container.get(5, []))
    return BuildSearchData(summaries=summaries)


def _parse_summaries(columns: list[dict[int, list[Any]]]) -> list[BuildSummary]:
    """Extract build summaries from protobuf columns."""
    column_map: dict[str, list[Any]] = {}
    for column in columns:
        name = _decode_string(column.get(1, []))
        if not name:
            continue
        column_map[name] = column.get(2, [])

    names = [_decode_string(value) for value in column_map.get("name", [])]
    accounts = [_decode_string(value) for value in column_map.get("account", [])]

    summaries: list[BuildSummary] = []
    for account, character in zip(accounts, names, strict=False):
        if account and character:
            summaries.append(BuildSummary(account=account, character=character))
    return summaries


def _decode_string(value: Any) -> str:
    """Decode a value to string from various protobuf representations."""
    if isinstance(value, dict):
        return "".join(_decode_string(entry) for entries in value.values() for entry in entries)
    if isinstance(value, list):
        return "".join(_decode_string(entry) for entry in value)
    if isinstance(value, bytes | bytearray):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        if 0 <= value <= 0x10FFFF:
            try:
                return chr(value)
            except ValueError:
                pass
        length = max(1, (value.bit_length() + 7) // 8)
        try:
            return value.to_bytes(length, "little").decode("utf-8", errors="replace").strip("\x00")
        except (OverflowError, ValueError):
            return ""
    return ""


def _parse_message(buffer: bytes) -> dict[int, list[Any]]:
    """Parse top-level protobuf message."""
    try:
        message, _ = _parse_message_internal(buffer, 0, len(buffer))
        return message
    except (IndexError, ValueError):
        return {}


def _parse_message_internal(
    buffer: bytes, start: int, end: int
) -> tuple[dict[int, list[Any]], int]:
    """Internal protobuf message parser."""
    pos = start
    fields: dict[int, list[Any]] = {}
    while pos < end:
        key, pos = _decode_varint(buffer, pos)
        field_number = key >> 3
        wire_type = key & 0x7

        value: Any
        if wire_type == _WIRE_VARINT:
            value, pos = _decode_varint(buffer, pos)
        elif wire_type == _WIRE_64BIT:
            value = int.from_bytes(buffer[pos : pos + 8], "little")
            pos += 8
        elif wire_type == _WIRE_LENGTH_DELIMITED:
            length, pos = _decode_varint(buffer, pos)
            chunk = buffer[pos : pos + length]
            pos += length
            nested, consumed = _try_parse_message(chunk)
            value = nested if consumed else chunk
        elif wire_type == _WIRE_START_GROUP:
            value, pos = _parse_group(buffer, pos, field_number)
        elif wire_type == _WIRE_END_GROUP:
            raise ValueError("Unexpected end-group marker")
        elif wire_type == _WIRE_32BIT:
            value = int.from_bytes(buffer[pos : pos + 4], "little")
            pos += 4
        else:
            raise ValueError(f"Unsupported wire type {wire_type}")

        fields.setdefault(field_number, []).append(value)

    return fields, pos


def _try_parse_message(chunk: bytes) -> tuple[dict[int, list[Any]], bool]:
    """Try to parse a chunk as a nested message."""
    try:
        message, consumed = _parse_message_internal(chunk, 0, len(chunk))
        if consumed == len(chunk) and any(key <= 3 for key in message):
            return message, True
    except (IndexError, ValueError):
        pass
    return {}, False


def _parse_group(buffer: bytes, pos: int, group_field: int) -> tuple[dict[int, list[Any]], int]:
    """Parse a protobuf group."""
    fields: dict[int, list[Any]] = {}
    while pos < len(buffer):
        key, pos = _decode_varint(buffer, pos)
        field_number = key >> 3
        wire_type = key & 0x7
        if wire_type == _WIRE_END_GROUP and field_number == group_field:
            break

        value, pos = _parse_value(buffer, pos, wire_type, field_number)
        fields.setdefault(field_number, []).append(value)
    return fields, pos


def _parse_value(buffer: bytes, pos: int, wire_type: int, field_number: int) -> tuple[Any, int]:
    """Parse a single protobuf value."""
    if wire_type == _WIRE_VARINT:
        return _decode_varint(buffer, pos)
    if wire_type == _WIRE_64BIT:
        value = int.from_bytes(buffer[pos : pos + 8], "little")
        return value, pos + 8
    if wire_type == _WIRE_LENGTH_DELIMITED:
        length, pos = _decode_varint(buffer, pos)
        chunk = buffer[pos : pos + length]
        pos += length
        nested, consumed = _try_parse_message(chunk)
        return (nested if consumed else chunk), pos
    if wire_type == _WIRE_START_GROUP:
        return _parse_group(buffer, pos, field_number)
    if wire_type == _WIRE_32BIT:
        value = int.from_bytes(buffer[pos : pos + 4], "little")
        return value, pos + 4
    raise ValueError(f"Unsupported wire type {wire_type}")


def _decode_varint(buffer: bytes, pos: int) -> tuple[int, int]:
    """Decode a protobuf varint."""
    shift = 0
    result = 0
    while True:
        value = buffer[pos]
        pos += 1
        result |= (value & 0x7F) << shift
        if not (value & 0x80):
            break
        shift += 7
    return result, pos
