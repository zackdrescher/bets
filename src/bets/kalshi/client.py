"""Wrapper around the async Kalshi SDK (`kalshi-python-async`).

The SDK is async; the CLI wraps calls with ``asyncio.run`` at the command boundary so the
CLI stays synchronous. Concrete SDK calls are marked with integration TODOs — the exact
method surface must be confirmed against the installed SDK version before wiring live.

NOTE: This wrapper NEVER decides to trade. It only executes an already-approved, capped,
confirmed order. All gating happens upstream (config env gate, risk caps, CLI confirmation).
"""

from __future__ import annotations

from dataclasses import dataclass

from bets.config import Settings
from bets.models import MarketQuote, Side

# The demo/prod base URLs differ; the gate lives in config.Settings.env.
_BASE_URLS = {
    "demo": "https://demo-api.kalshi.co",
    "prod": "https://api.elections.kalshi.com",
}


@dataclass
class OrderResult:
    accepted: bool
    exchange_order_id: str | None
    detail: str


class KalshiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = _BASE_URLS["prod" if settings.is_prod else "demo"]
        self._key_id, self._key_path = settings.active_credentials()
        # TODO(integration): construct the kalshi-python-async client here with
        # (self.base_url, self._key_id, self._key_path). Confirm the constructor signature
        # against the installed SDK version.
        self._sdk = None

    async def get_quote(self, ticker: str) -> MarketQuote:
        """Fetch a market and return a normalized quote (YES price as 0-1)."""
        # TODO(integration): call the SDK market endpoint, map its yes bid/ask/last to a
        # single yes_price in 0-1. Kalshi prices are integer cents 0-100.
        raise NotImplementedError("wire kalshi-python-async get_market here")

    async def list_positions(self) -> list[dict]:
        """Authoritative open positions from Kalshi (source of truth for positions)."""
        # TODO(integration): call the SDK positions endpoint.
        raise NotImplementedError("wire kalshi-python-async get_positions here")

    async def place_order(
        self,
        *,
        ticker: str,
        side: Side,
        contracts: int,
        price_cents: int,
        idempotency_key: str,
    ) -> OrderResult:
        """Submit a single order. Caller MUST have passed env gate, caps, and confirmation.

        The idempotency key is forwarded to the exchange (and recorded in the audit log) so a
        retry after a crash cannot double-submit.
        """
        # TODO(integration): call the SDK create_order endpoint with client_order_id set to
        # idempotency_key. Map (side, contracts, price_cents) to the SDK's order schema.
        raise NotImplementedError("wire kalshi-python-async create_order here")

    async def cancel_all(self) -> int:
        """Kill-switch: cancel all resting orders. Returns count cancelled."""
        # TODO(integration): list resting orders and cancel each via the SDK.
        raise NotImplementedError("wire kalshi-python-async cancel here")
