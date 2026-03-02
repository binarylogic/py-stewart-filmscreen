from stewart_filmscreen.protocol import build_command, build_query, parse_frame


def test_build_command_without_value() -> None:
    assert build_command("1.1.1.MOTOR", "UP") == "#1.1.1.MOTOR=UP;"


def test_build_command_with_value() -> None:
    assert build_command("1.1.0.MOTOR", "RECALL", value=3) == "#1.1.0.MOTOR=RECALL,3;"


def test_build_query() -> None:
    assert build_query("1.1.1.MOTOR", "POSITION") == "#1.1.1.MOTOR.POSITION=?;"


def test_parse_event_position() -> None:
    msg = parse_frame("!1.1.1.MOTOR.POSITION=43;")
    assert msg is not None
    assert msg.kind == "event"
    assert msg.motor == "1.1.1.MOTOR"
    assert msg.name == "POSITION"
    assert msg.value == "43"


def test_parse_command_recall() -> None:
    msg = parse_frame("#1.1.0.MOTOR=RECALL,4;")
    assert msg is not None
    assert msg.kind == "command"
    assert msg.name == "RECALL"
    assert msg.value == "4"


def test_parse_query() -> None:
    msg = parse_frame("#1.1.1.MOTOR.POSITION=?;")
    assert msg is not None
    assert msg.kind == "query"
    assert msg.name == "POSITION"
    assert msg.value is None


def test_parse_unknown_returns_none() -> None:
    assert parse_frame("garbage") is None
