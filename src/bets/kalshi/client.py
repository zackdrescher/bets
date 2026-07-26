"""Kalshi client port — the only seam the real SDK is wired behind.

`kalshi-python-async` is async; callers bridge to it with `asyncio.run()` at the
CLI command boundary so the CLI surface stays synchronous (ADR 0001 D8).

Every method raises `NotImplementedError` until the SDK is wired behind this
port (tracked in issue #8).
"""

from __future__ import annotations

from typing import Protocol

from bets.models import MarketQuote


class KalshiClient(Protocol):
    """Boundary port to the Kalshi exchange. All methods are async."""

    async def get_quote(self, ticker: str) -> MarketQuote: ...

    async def list_positions(self) -> list[dict]: ...

    async def place_order(
        self,
        *,
        ticker: str,
        side: str,
        contracts: int,
        price_cents: int,
        idempotency_key: str,
    ) -> dict: ...

    async def cancel_all(self) -> None: ...


class UnwiredKalshiClient:
    """Default `KalshiClient`: every method raises until the SDK is wired (#8)."""

    async def get_quote(self, ticker: str) -> MarketQuote:
        raise NotImplementedError("Kalshi SDK is not yet wired; see issue #8")

    async def list_positions(self) -> list[dict]:
        raise NotImplementedError("Kalshi SDK is not yet wired; see issue #8")

    async def place_order(
        self,
        *,
        ticker: str,
        side: str,
        contracts: int,
        price_cents: int,
        idempotency_key: str,
    ) -> dict:
        raise NotImplementedError("Kalshi SDK is not yet wired; see issue #8")

    async def cancel_all(self) -> None:
        raise NotImplementedError("Kalshi SDK is not yet wired; see issue #8")
