"""Spend-cap enforcement. Sits between a Recommendation and any real order.

Pure/deterministic given inputs so it can be unit-tested without a DB or network.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapResult:
    approved: bool
    allowed_cents: int
    reason: str


def check_spend_caps(
    stake_cents: int,
    *,
    max_order_cents: int,
    max_daily_cents: int,
    spent_today_cents: int,
) -> CapResult:
    """Enforce per-order and per-day spend caps.

    Fails closed: a non-positive stake or an exhausted daily budget is rejected.
    Never returns an ``allowed_cents`` above the requested stake.
    """
    if stake_cents <= 0:
        return CapResult(False, 0, "stake is non-positive")

    if stake_cents > max_order_cents:
        return CapResult(
            False,
            max_order_cents,
            f"stake {stake_cents}c exceeds per-order cap {max_order_cents}c",
        )

    remaining_daily = max_daily_cents - spent_today_cents
    if remaining_daily <= 0:
        return CapResult(False, 0, f"daily cap {max_daily_cents}c already reached")

    if stake_cents > remaining_daily:
        return CapResult(
            False,
            remaining_daily,
            f"stake {stake_cents}c exceeds remaining daily budget {remaining_daily}c",
        )

    return CapResult(True, stake_cents, "within caps")
