"""Fractional-Kelly sizing. Pure function, no I/O. See docs/strategies/kelly.md.

f* = (q - p) / (1 - p)   # full-Kelly fraction of bankroll for a YES buy
Negative edge mirrors to the NO side using q_no = 1 - q, p_no = 1 - p.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from bets.models import Estimate, MarketQuote, Recommendation, Side


def _no_bet(
    ticker: str, side: Side, edge: float, price_cents: int, rationale: str
) -> Recommendation:
    return Recommendation(
        ticker=ticker,
        side=side,
        edge=edge,
        contracts=0,
        stake_cents=0,
        price_cents=price_cents,
        rationale=rationale,
    )


def kelly_recommendation(
    quote: MarketQuote,
    estimate: Estimate,
    bankroll_cents: int,
    *,
    kelly_fraction: float,
    edge_threshold: float,
) -> Recommendation:
    edge = estimate.prob_yes - quote.yes_price

    if abs(edge) < edge_threshold:
        side = Side.YES if edge >= 0 else Side.NO
        price = quote.yes_price if side is Side.YES else quote.no_price
        return _no_bet(
            quote.ticker,
            side,
            edge,
            round(price * 100),
            f"edge {edge:+.3f} below threshold {edge_threshold:.3f}; no bet",
        )

    if edge > 0:
        side, p_eff, q_eff = Side.YES, quote.yes_price, estimate.prob_yes
    else:
        side, p_eff, q_eff = Side.NO, quote.no_price, 1.0 - estimate.prob_yes

    price_cents = round(p_eff * 100)
    full_kelly = (q_eff - p_eff) / (1.0 - p_eff)
    stake_fraction = kelly_fraction * full_kelly

    if stake_fraction <= 0 or price_cents <= 0:
        return _no_bet(
            quote.ticker, side, edge, price_cents, "Kelly fraction non-positive; no bet"
        )

    raw_stake_cents = stake_fraction * bankroll_cents
    contracts = math.floor(raw_stake_cents / price_cents)
    stake_cents = contracts * price_cents

    rationale = (
        f"edge {edge:+.3f} clears threshold {edge_threshold:.3f}; "
        f"full-Kelly f*={full_kelly:.3f}, {kelly_fraction:.2f}x-Kelly stake"
    )

    return Recommendation(
        ticker=quote.ticker,
        side=side,
        edge=edge,
        contracts=contracts,
        stake_cents=stake_cents,
        price_cents=price_cents,
        rationale=rationale,
    )


@dataclass(frozen=True)
class KellyStrategy:
    """Strategy interface implementation backed by fractional Kelly sizing."""

    kelly_fraction: float = 0.25
    edge_threshold: float = 0.05

    def evaluate(
        self, quote: MarketQuote, estimate: Estimate, bankroll_cents: int
    ) -> Recommendation:
        return kelly_recommendation(
            quote,
            estimate,
            bankroll_cents,
            kelly_fraction=self.kelly_fraction,
            edge_threshold=self.edge_threshold,
        )
