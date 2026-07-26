"""Kelly sizing math. See docs/strategies/kelly.md for the worked example."""

import math

from bets.models import Estimate, MarketQuote, Side
from bets.strategy.base import StrategyConfig
from bets.strategy.kelly import KellyStrategy, full_kelly_fraction


def test_full_kelly_matches_formula():
    # f* = (q - p) / (1 - p)
    assert math.isclose(full_kelly_fraction(0.65, 0.55), 0.10 / 0.45, rel_tol=1e-9)


def test_no_edge_is_zero_fraction():
    assert full_kelly_fraction(0.5, 0.5) == 0.0


def test_negative_edge_mirrors_to_no_side():
    # q < p => YES has negative edge; NO side has positive edge of same magnitude structure.
    f = full_kelly_fraction(0.40, 0.55)
    assert f > 0  # positive fraction, to be staked on NO


def test_worked_example_quarter_kelly():
    strat = KellyStrategy(StrategyConfig(kelly_fraction=0.25, edge_threshold=0.05))
    quote = MarketQuote(ticker="TEST", yes_price=0.55)
    est = Estimate(ticker="TEST", prob_yes=0.65)
    rec = strat.evaluate(quote, est, bankroll_cents=100_000)

    assert rec.side is Side.YES
    assert math.isclose(rec.edge, 0.10, rel_tol=1e-9)
    # stake ~ 0.25 * 0.2222 * $1000 = ~$55.6 -> 101 contracts @ 55c
    assert rec.price_cents == 55
    assert rec.contracts == 101
    assert rec.stake_cents == 101 * 55


def test_below_threshold_is_not_actionable():
    strat = KellyStrategy(StrategyConfig(kelly_fraction=0.25, edge_threshold=0.05))
    quote = MarketQuote(ticker="TEST", yes_price=0.55)
    est = Estimate(ticker="TEST", prob_yes=0.57)  # edge 0.02 < 0.05
    rec = strat.evaluate(quote, est, bankroll_cents=100_000)
    assert not rec.actionable
    assert rec.contracts == 0


def test_worst_case_loss_is_premium():
    strat = KellyStrategy(StrategyConfig(kelly_fraction=0.25, edge_threshold=0.05))
    quote = MarketQuote(ticker="TEST", yes_price=0.55)
    est = Estimate(ticker="TEST", prob_yes=0.65)
    rec = strat.evaluate(quote, est, bankroll_cents=100_000)
    assert rec.worst_case_loss_cents == rec.price_cents * rec.contracts


def test_negative_edge_recommends_no_side():
    strat = KellyStrategy(StrategyConfig(kelly_fraction=0.25, edge_threshold=0.05))
    quote = MarketQuote(ticker="TEST", yes_price=0.55)
    est = Estimate(ticker="TEST", prob_yes=0.40)  # edge -0.15
    rec = strat.evaluate(quote, est, bankroll_cents=100_000)
    assert rec.side is Side.NO
    assert rec.actionable
    assert rec.price_cents == 45  # no_price = 1 - 0.55
