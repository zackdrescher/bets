"""Swappable position-sizing strategies. See docs/strategies/kelly.md for the default."""

from __future__ import annotations

from typing import Protocol

from bets.models import Estimate, MarketQuote, Recommendation


class Strategy(Protocol):
    """Turns a market quote + the user's estimate into a Recommendation.

    Implementations must be pure with respect to sizing math: no I/O.
    """

    def evaluate(
        self, quote: MarketQuote, estimate: Estimate, bankroll_cents: int
    ) -> Recommendation: ...
