"""High-level async client with reconnect and callback support."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .const import (
    COMMAND_DOWN,
    COMMAND_RECALL,
    COMMAND_STOP,
    COMMAND_STORE,
    COMMAND_UP,
    DEFAULT_COMMAND_THROTTLE_SECONDS,
    DEFAULT_PORT,
    DEFAULT_RECONNECT_SECONDS,
    MOTOR_ALL,
)
from .exceptions import ConnectionFailedError
from .models import ProtocolMessage
from .protocol import build_command, build_query, parse_frame
from .transport import StewartTelnetTransport

log = logging.getLogger(__name__)

StateCallback = Callable[[ProtocolMessage], Awaitable[None] | None]


@dataclass
class RuntimeState:
    """Mutable runtime state mirrored from protocol events."""

    last_position_by_motor: dict[str, int] = field(default_factory=dict)
    last_status_by_motor: dict[str, str] = field(default_factory=dict)


class StewartFilmscreenClient:
    """Client that maintains authenticated connection and dispatches parsed frames."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        port: int = DEFAULT_PORT,
        reconnect_seconds: float = DEFAULT_RECONNECT_SECONDS,
        command_throttle_seconds: float = DEFAULT_COMMAND_THROTTLE_SECONDS,
        transport: StewartTelnetTransport | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._username = username
        self._password = password
        self._reconnect_seconds = reconnect_seconds
        self._command_throttle_seconds = command_throttle_seconds

        self._transport = transport or StewartTelnetTransport(host, port, username, password)

        self._authenticated = asyncio.Event()
        self._running = False
        self._read_task: asyncio.Task[None] | None = None
        self._connect_task: asyncio.Task[None] | None = None
        self._command_queue_task: asyncio.Task[None] | None = None
        self._command_queue: asyncio.Queue[str] = asyncio.Queue()

        self.state = RuntimeState()
        self._callbacks: list[StateCallback] = []

    @property
    def connected(self) -> bool:
        return self._transport.connected

    def register_callback(self, callback: StateCallback) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def deregister_callback(self, callback: StateCallback) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._connect_task = asyncio.create_task(self._connection_loop())
        self._command_queue_task = asyncio.create_task(self._command_loop())

    async def wait_authenticated(self, timeout: float | None = 10.0) -> None:
        await asyncio.wait_for(self._authenticated.wait(), timeout=timeout)

    async def stop_client(self) -> None:
        self._running = False
        self._authenticated.clear()
        for task in (self._connect_task, self._read_task, self._command_queue_task):
            if task is not None:
                task.cancel()
        await self._transport.close()

    async def _connection_loop(self) -> None:
        while self._running:
            if self.connected:
                await asyncio.sleep(0.25)
                continue
            try:
                await self._transport.connect()
                self._authenticated.set()
                self._read_task = asyncio.create_task(self._read_loop())
            except Exception as err:  # noqa: BLE001
                self._authenticated.clear()
                log.debug("Connection failed: %s", err)
                await asyncio.sleep(self._reconnect_seconds)

    async def _read_loop(self) -> None:
        try:
            async for line in self._transport.iter_lines():
                msg = parse_frame(line)
                if msg is None:
                    continue
                self._apply_state(msg)
                await self._emit(msg)
        except Exception as err:  # noqa: BLE001
            log.debug("Read loop stopped: %s", err)
        finally:
            self._authenticated.clear()

    async def _command_loop(self) -> None:
        while self._running:
            cmd = await self._command_queue.get()
            await self._authenticated.wait()
            try:
                await self._transport.write_line(cmd)
            except ConnectionFailedError:
                # Requeue and let reconnect loop recover.
                await asyncio.sleep(self._reconnect_seconds)
                await self._command_queue.put(cmd)
            await asyncio.sleep(self._command_throttle_seconds)

    def _apply_state(self, msg: ProtocolMessage) -> None:
        if msg.kind == "event" and msg.name == "POSITION" and msg.value is not None:
            with contextlib.suppress(ValueError):
                self.state.last_position_by_motor[msg.motor] = int(round(float(msg.value)))
        if msg.kind == "event" and msg.name == "STATUS" and msg.value is not None:
            self.state.last_status_by_motor[msg.motor] = msg.value

    async def _emit(self, msg: ProtocolMessage) -> None:
        for cb in tuple(self._callbacks):
            try:
                out = cb(msg)
                if inspect.isawaitable(out):
                    await out
            except Exception:  # noqa: BLE001
                log.exception("state callback failed")

    async def send_raw(self, line: str) -> None:
        await self._command_queue.put(line)

    async def send_command(self, motor: str, command: str, value: int | str | None = None) -> None:
        await self.send_raw(build_command(motor, command, value=value))

    async def query_position(self, motor: str) -> None:
        await self.send_raw(build_query(motor, "POSITION"))

    async def move_up(self, motor: str) -> None:
        await self.send_command(motor, COMMAND_UP)

    async def move_down(self, motor: str) -> None:
        await self.send_command(motor, COMMAND_DOWN)

    async def stop(self, motor: str) -> None:
        await self.send_command(motor, COMMAND_STOP)

    async def recall_preset(self, preset_number: int) -> None:
        await self.send_command(MOTOR_ALL, COMMAND_RECALL, value=preset_number)

    async def store_preset(self, preset_number: int) -> None:
        await self.send_command(MOTOR_ALL, COMMAND_STORE, value=preset_number)
