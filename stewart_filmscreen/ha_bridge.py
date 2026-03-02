"""Helpers for mapping Stewart protocol messages into HA-friendly payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import ProtocolMessage

BridgeEventKind = Literal["motor_position", "motor_status", "protocol_message"]


@dataclass(frozen=True)
class BridgeEvent:
    """Integration-friendly event payload."""

    kind: BridgeEventKind
    motor: str
    value: str | int | None
    raw: ProtocolMessage


def to_ha_event(message: ProtocolMessage) -> BridgeEvent:
    """Convert a protocol message into a high-level bridge event."""
    if message.kind == "event" and message.name == "POSITION":
        value: str | int | None = message.value
        if message.value is not None:
            try:
                value = int(round(float(message.value)))
            except ValueError:
                value = message.value
        return BridgeEvent(kind="motor_position", motor=message.motor, value=value, raw=message)

    if message.kind == "event" and message.name == "STATUS":
        return BridgeEvent(kind="motor_status", motor=message.motor, value=message.value, raw=message)

    return BridgeEvent(kind="protocol_message", motor=message.motor, value=message.value, raw=message)
