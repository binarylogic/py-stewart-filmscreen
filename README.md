# Stewart Filmscreen Python Library

Async Stewart Filmscreen CVM client for long-running integrations (Home Assistant primary target).

## Status

This is a clean implementation focused on reliability, explicit typing, and deterministic parsing.

Protocol reference used:
- https://www.stewartfilmscreen.com/Files/files/Support%20Material/Controls/CVM.pdf

## Installation

```bash
pip install stewart-filmscreen
```

## Quick Start

```python
import asyncio

from stewart_filmscreen.client import StewartFilmscreenClient


async def main() -> None:
    client = StewartFilmscreenClient(
        host="192.168.1.50",
        username="your_username",
        password="your_password",
    )

    try:
        await client.start()
        await client.wait_authenticated(timeout=10)

        await client.move_down("1.1.1.MOTOR")
        await client.stop("1.1.1.MOTOR")
        await client.recall_preset(3)
    finally:
        await client.stop_client()


asyncio.run(main())
```

## Development

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run ty check stewart_filmscreen
uv run pytest -v
```

## Real Device Integration Tests (Read-Only)

The test suite includes a manual, read-only integration tier for validating behavior against a real CVM.

- Marker: `integration_real`
- Opt-in gate: `STEWART_ITEST=1`
- Target host: `STEWART_HOST=<ip-or-hostname>`
- Optional port override: `STEWART_PORT=23`
- Credentials: `STEWART_USERNAME`, `STEWART_PASSWORD`
- Optional metadata: `STEWART_MAC`
- If the device is offline/unreachable, tests are skipped.

Set up local env:

```bash
cp .env.example .env
```

Run the real-device tests:

```bash
set -a && source .env && set +a && uv run pytest -v -m integration_real
```
