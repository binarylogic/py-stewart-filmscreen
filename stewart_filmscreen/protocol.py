"""Protocol message building and parsing."""

from __future__ import annotations

from .const import POSTFIX, PREFIX_COMMAND, PREFIX_EVENT
from .models import ProtocolMessage


def build_command(motor: str, command: str, value: int | str | None = None) -> str:
    """Build command frame, optionally with an argument."""
    frame = f"{PREFIX_COMMAND}{motor}={command}"
    if value is not None:
        frame = f"{frame},{value}"
    return f"{frame}{POSTFIX}"


def build_query(motor: str, query: str) -> str:
    """Build query frame."""
    return f"{PREFIX_COMMAND}{motor}.{query}=?{POSTFIX}"


def parse_frame(frame: str) -> ProtocolMessage | None:
    """Parse command/event/query frame. Unknown formats return None."""
    raw = frame.strip()
    if not raw:
        return None
    if raw[0] not in (PREFIX_COMMAND, PREFIX_EVENT):
        return None
    if not raw.endswith(POSTFIX):
        return None

    body = raw[1:-1]
    motor_marker = ".MOTOR"
    idx = body.find(motor_marker)
    if idx <= 0:
        return None

    motor = body[: idx + len(motor_marker)]
    rest = body[idx + len(motor_marker) :]

    if raw[0] == PREFIX_EVENT:
        return _parse_event(raw, motor, rest)
    if rest.startswith("."):
        return _parse_query(raw, motor, rest)
    if rest.startswith("="):
        return _parse_command(raw, motor, rest)
    return None


def _parse_event(raw: str, motor: str, rest: str) -> ProtocolMessage | None:
    if not rest.startswith(".") or "=" not in rest:
        return None
    name, value = rest[1:].split("=", 1)
    name = name.strip()
    value = value.strip()
    if not name:
        return None
    return ProtocolMessage(kind="event", motor=motor, name=name, value=value or None, raw=raw)


def _parse_query(raw: str, motor: str, rest: str) -> ProtocolMessage | None:
    payload = rest[1:]
    if "=" not in payload:
        return None
    name, value = payload.split("=", 1)
    name = name.strip()
    value = value.strip()
    if not name:
        return None
    return ProtocolMessage(kind="query", motor=motor, name=name, value=None if value == "?" else value, raw=raw)


def _parse_command(raw: str, motor: str, rest: str) -> ProtocolMessage | None:
    payload = rest[1:]
    if "," in payload:
        name, value = payload.split(",", 1)
        name = name.strip()
        value = value.strip()
    else:
        name = payload.strip()
        value = None
    if not name:
        return None
    return ProtocolMessage(kind="command", motor=motor, name=name, value=value, raw=raw)
