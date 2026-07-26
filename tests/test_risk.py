"""Spend-cap enforcement — fails closed."""

from bets.risk import check_spend_caps


def _caps(stake, spent=0, order=5_000, daily=20_000):
    return check_spend_caps(
        stake, max_order_cents=order, max_daily_cents=daily, spent_today_cents=spent
    )


def test_within_caps_approved():
    r = _caps(4_000)
    assert r.approved
    assert r.allowed_cents == 4_000


def test_exceeds_per_order_cap_rejected():
    r = _caps(6_000)
    assert not r.approved
    assert r.allowed_cents == 5_000


def test_exceeds_remaining_daily_rejected():
    r = _caps(4_000, spent=18_000)  # only 2_000 left
    assert not r.approved
    assert r.allowed_cents == 2_000


def test_daily_budget_exhausted_rejected():
    r = _caps(1_000, spent=20_000)
    assert not r.approved
    assert r.allowed_cents == 0


def test_non_positive_stake_rejected():
    assert not _caps(0).approved
    assert not _caps(-100).approved
