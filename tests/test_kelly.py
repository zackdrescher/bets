"""Kelly sizing is a pure function: no I/O, deterministic given quote/estimate/bankroll."""

import pytest

from bets.models import Estimate, MarketQuote, Side
from bets.strategy.kelly import KellyStrategy, kelly_recommendation

BANKROLL_CENTS = 100_000  # $1,000
KELLY_FRACTION = 0.25
EDGE_THRESHOLD = 0.05


def _rec(yes_price: float, prob_yes: float, bankroll_cents: int = BANKROLL_CENTS):
    quote = MarketQuote(ticker="TICK", yes_price=yes_price)
    estimate = Estimate(ticker="TICK", prob_yes=prob_yes)
    return kelly_recommendation(
        quote,
        estimate,
        bankroll_cents,
        kelly_fraction=KELLY_FRACTION,
        edge_threshold=EDGE_THRESHOLD,
    )


def test_worked_example_from_docs():
    # p=0.55, q=0.65, quarter-Kelly, $1,000 bankroll -> YES, 101 contracts @ 55c
    rec = _rec(yes_price=0.55, prob_yes=0.65)
    assert rec.side is Side.YES
    assert rec.price_cents == 55
    assert rec.contracts == 101
    assert rec.actionable


def test_positive_edge_recommends_yes():
    rec = _rec(yes_price=0.40, prob_yes=0.60)
    assert rec.side is Side.YES
    assert rec.edge == pytest.approx(0.20)
    assert rec.contracts > 0


def test_negative_edge_mirrors_to_no():
    # q < p by more than threshold -> NO side has the edge
    rec = _rec(yes_price=0.60, prob_yes=0.40)
    assert rec.side is Side.NO
    assert rec.edge == pytest.approx(-0.20)
    assert rec.price_cents == 40  # no_price = 1 - 0.60
    assert rec.contracts > 0


def test_sub_threshold_edge_is_not_actionable():
    rec = _rec(yes_price=0.50, prob_yes=0.52)  # edge = 0.02 < 0.05 threshold
    assert rec.contracts == 0
    assert rec.stake_cents == 0
    assert not rec.actionable


def test_edge_exactly_at_threshold_is_actionable():
    rec = _rec(yes_price=0.50, prob_yes=0.55)  # edge = 0.05 == threshold
    assert rec.actionable


def test_zero_edge_is_not_actionable():
    rec = _rec(yes_price=0.50, prob_yes=0.50)
    assert rec.contracts == 0
    assert not rec.actionable


def test_stake_rounds_down_to_whole_contracts():
    rec = _rec(yes_price=0.55, prob_yes=0.65)
    assert isinstance(rec.contracts, int)
    # 101 contracts @ 55c = 5555 cents, strictly <= raw stake of ~5556 cents
    assert rec.stake_cents == rec.contracts * rec.price_cents
    assert rec.stake_cents <= 5556


def test_worst_case_loss_is_premium_paid():
    rec = _rec(yes_price=0.55, prob_yes=0.65)
    assert rec.worst_case_loss_cents == rec.contracts * rec.price_cents


def test_zero_price_side_yields_no_bet():
    # price_cents == 0 makes stake sizing (division by price) meaningless; must not bet
    rec = _rec(yes_price=0.0, prob_yes=0.06)
    assert rec.price_cents == 0
    assert rec.contracts == 0
    assert not rec.actionable


def test_strategy_class_delegates_to_pure_function():
    strategy = KellyStrategy(kelly_fraction=KELLY_FRACTION, edge_threshold=EDGE_THRESHOLD)
    quote = MarketQuote(ticker="TICK", yes_price=0.55)
    estimate = Estimate(ticker="TICK", prob_yes=0.65)
    rec = strategy.evaluate(quote, estimate, BANKROLL_CENTS)
    assert rec.side is Side.YES
    assert rec.contracts == 101


def test_strategy_defaults_match_docs():
    strategy = KellyStrategy()
    assert strategy.kelly_fraction == 0.25
    assert strategy.edge_threshold == 0.05
