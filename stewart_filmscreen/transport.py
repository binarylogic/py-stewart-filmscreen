"""Async transport for Stewart CVM Telnet endpoint."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .const import PROMPT_CONNECTED, PROMPT_PASSWORD, PROMPT_USER
from .exceptions import AuthenticationError, ConnectionFailedError


class StewartTelnetTransport:
    """Telnet-ish text transport with prompt-based authentication."""

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_lock = asyncio.Lock()

    async def connect(self, timeout: float = 10.0) -> None:
        """Open socket and run prompt-based login."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=timeout
            )
        except Exception as err:  # noqa: BLE001
            raise ConnectionFailedError(str(err)) from err

        await self._authenticate(timeout=timeout)

    async def _authenticate(self, timeout: float) -> None:
        if self._reader is None or self._writer is None:
            raise ConnectionFailedError("transport not connected")

        for _ in range(6):
            token = await asyncio.wait_for(self._reader.readuntil(b":"), timeout=timeout)
            text = token.decode("utf-8", errors="ignore")
            if text.endswith(PROMPT_USER):
                self._writer.write((self._username + "\r\n").encode())
                await self._writer.drain()
                continue
            if text.endswith(PROMPT_PASSWORD):
                self._writer.write((self._password + "\r\n").encode())
                await self._writer.drain()
                continue
            if text.endswith(PROMPT_CONNECTED):
                return
        raise AuthenticationError("did not receive connected prompt")

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def write_line(self, line: str) -> None:
        if self._writer is None:
            raise ConnectionFailedError("transport is not connected")
        self._writer.write((line + "\r\n").encode("utf-8"))
        await self._writer.drain()

    async def iter_lines(self) -> AsyncIterator[str]:
        if self._reader is None:
            raise ConnectionFailedError("transport is not connected")
        while True:
            async with self._read_lock:
                data = await self._reader.readline()
            if not data:
                break
            yield data.decode("utf-8", errors="ignore").strip()

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None
