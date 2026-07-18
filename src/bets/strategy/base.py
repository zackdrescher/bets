"""Strategy interface. Implementations map (quote, estimate, bankroll) -> Recommendation.

Strategies MUST be pure: no I/O, no network, no DB. This keeps sizing math testable and
swappable. Spend caps and confirmation live outside the strategy (see store / cli).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from bets.models import Estimate, MarketQuote, Recommendation


class StrategyConfig(BaseModel):
    """Tunables shared by strategies."""

    kelly_fraction: float = Field(default=0.25, gt=0.0, le=1.0)
    edge_threshold: float = Field(default=0.05, ge=0.0, le=1.0)


@runtime_checkable
class Strategy(Protocol):
    name: str

    def evaluate(
        self, quote: MarketQuote, estimate: Estimate, bankroll_cents: int
    ) -> Recommendation:
        """Return a sizing recommendation. Pure function — no side effects."""
        ...
