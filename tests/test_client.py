import asyncio

import pytest

from stewart_filmscreen.client import StewartFilmscreenClient
from stewart_filmscreen.models import ProtocolMessage


class FakeTransport:
    def __init__(self) -> None:
        self._connected = False
        self.writes: list[str] = []
        self._incoming: asyncio.Queue[str] = asyncio.Queue()

    async def connect(self, timeout: float = 10.0) -> None:
        self._connected = True

    @property
    def connected(self) -> bool:
        return self._connected

    async def write_line(self, line: str) -> None:
        self.writes.append(line)

    async def iter_lines(self):
        while self._connected:
            line = await self._incoming.get()
            if line == "__STOP__":
                break
            yield line

    async def close(self) -> None:
        self._connected = False
        await self._incoming.put("__STOP__")

    async def feed(self, line: str) -> None:
        await self._incoming.put(line)


@pytest.mark.asyncio
async def test_client_sends_commands_and_updates_state() -> None:
    transport = FakeTransport()
    client = StewartFilmscreenClient(
        host="127.0.0.1",
        username="u",
        password="p",
        transport=transport,  # type: ignore[arg-type]
        command_throttle_seconds=0.0,
    )

    seen: list[ProtocolMessage] = []

    def _on_msg(msg: ProtocolMessage) -> None:
        seen.append(msg)

    client.register_callback(_on_msg)

    await client.start()
    await client.wait_authenticated(timeout=1)

    await client.move_up("1.1.1.MOTOR")
    await client.recall_preset(2)
    await asyncio.sleep(0.05)

    assert "#1.1.1.MOTOR=UP;" in transport.writes
    assert "#1.1.0.MOTOR=RECALL,2;" in transport.writes

    await transport.feed("!1.1.1.MOTOR.POSITION=37;")
    await transport.feed("!1.1.1.MOTOR.STATUS=STOP;")
    await asyncio.sleep(0.05)

    assert client.state.last_position_by_motor["1.1.1.MOTOR"] == 37
    assert client.state.last_status_by_motor["1.1.1.MOTOR"] == "STOP"
    assert any(m.name == "POSITION" for m in seen)

    await client.stop_client()


@pytest.mark.asyncio
async def test_client_emits_connection_callbacks() -> None:
    transport = FakeTransport()
    client = StewartFilmscreenClient(
        host="127.0.0.1",
        username="u",
        password="p",
        transport=transport,  # type: ignore[arg-type]
        command_throttle_seconds=0.0,
    )

    events: list[str] = []
    client.register_connection_callback(events.append)

    await client.start()
    await client.wait_authenticated(timeout=1)
    await asyncio.sleep(0)

    assert events == ["connected"]

    await transport.close()
    await asyncio.sleep(0.05)

    assert events == ["connected", "disconnected"]

    await client.stop_client()
