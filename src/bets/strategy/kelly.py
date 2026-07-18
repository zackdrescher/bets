"""Fractional Kelly sizing. See docs/strategies/kelly.md for the derivation.

Pure functions only — no I/O. Spend caps are applied downstream, not here.
"""

from __future__ import annotations

from bets.models import Estimate, MarketQuote, Recommendation, Side
from bets.strategy.base import StrategyConfig


def full_kelly_fraction(q: float, p: float) -> float:
    """Full-Kelly fraction of bankroll for a binary contract buy.

    f* = (q - p) / (1 - p) for the YES side. Returns the fraction for the *better* side;
    callers decide the side from the sign of the edge. Guards degenerate prices.
    """
    edge = q - p
    if edge >= 0:
        denom = 1.0 - p
        return 0.0 if denom <= 0 else edge / denom
    # Negative edge on YES => positive edge on NO. Mirror the formula for the NO side.
    q_no, p_no = 1.0 - q, 1.0 - p
    denom = 1.0 - p_no
    return 0.0 if denom <= 0 else (q_no - p_no) / denom


class KellyStrategy:
    """Fractional Kelly with an edge threshold."""

    name = "kelly"

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def evaluate(
        self, quote: MarketQuote, estimate: Estimate, bankroll_cents: int
    ) -> Recommendation:
        q = estimate.prob_yes
        p = quote.yes_price
        edge = q - p

        # Pick side and its price.
        if edge >= 0:
            side, price = Side.YES, p
        else:
            side, price = Side.NO, quote.no_price

        # Below-threshold edges are treated as noise -> no position.
        if abs(edge) < self.config.edge_threshold:
            return Recommendation(
                ticker=quote.ticker,
                side=side,
                edge=edge,
                contracts=0,
                stake_cents=0,
                price_cents=_to_cents(price),
                rationale=(
                    f"edge {edge:+.3f} below threshold "
                    f"{self.config.edge_threshold:.3f}; no bet"
                ),
            )

        f_star = full_kelly_fraction(q, p)
        stake_fraction = self.config.kelly_fraction * f_star
        stake_cents = int(round(stake_fraction * bankroll_cents))

        price_cents = _to_cents(price)
        contracts = stake_cents // price_cents if price_cents > 0 else 0
        # Actual stake after integer contract rounding.
        actual_stake_cents = contracts * price_cents

        return Recommendation(
            ticker=quote.ticker,
            side=side,
            edge=edge,
            contracts=contracts,
            stake_cents=actual_stake_cents,
            price_cents=price_cents,
            rationale=(
                f"{side.value.upper()} edge {edge:+.3f}, "
                f"f*={f_star:.3f}, {self.config.kelly_fraction:.2f}-Kelly "
                f"-> {contracts} contracts @ {price_cents}c"
            ),
        )


def _to_cents(prob: float) -> int:
    """Convert a 0-1 price to integer cents 0-100."""
    return max(0, min(100, int(round(prob * 100))))
