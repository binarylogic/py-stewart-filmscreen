"""Typed protocol models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MessageKind = Literal["command", "event", "query"]
MotorID = Literal[
    "1.1.0.MOTOR",
    "1.1.1.MOTOR",
    "1.1.2.MOTOR",
    "1.1.3.MOTOR",
    "1.1.4.MOTOR",
]
CommandName = Literal["UP", "DOWN", "STOP", "RETRACT", "RECALL", "STORE"]
EventName = Literal["STATUS", "POSITION"]
QueryName = Literal["POSITION"]
MessageName = CommandName | EventName | QueryName


@dataclass(frozen=True)
class ProtocolMessage:
    """Parsed protocol frame."""

    kind: MessageKind
    motor: MotorID | str
    name: MessageName | str
    value: str | None
    raw: str
