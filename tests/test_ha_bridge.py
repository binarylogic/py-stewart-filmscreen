from stewart_filmscreen.ha_bridge import to_ha_event
from stewart_filmscreen.models import ProtocolMessage


def test_bridge_position_event() -> None:
    msg = ProtocolMessage(kind="event", motor="1.1.1.MOTOR", name="POSITION", value="42", raw="!1.1.1.MOTOR.POSITION=42;")
    event = to_ha_event(msg)
    assert event.kind == "motor_position"
    assert event.value == 42


def test_bridge_status_event() -> None:
    msg = ProtocolMessage(kind="event", motor="1.1.1.MOTOR", name="STATUS", value="STOP", raw="!1.1.1.MOTOR.STATUS=STOP;")
    event = to_ha_event(msg)
    assert event.kind == "motor_status"
    assert event.value == "STOP"
