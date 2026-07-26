"""Typer app — CLI command wiring.

The Kalshi SDK is async; commands wrap async work with asyncio.run() so this
surface stays synchronous.
"""

from __future__ import annotations

import asyncio

import typer

from bets.config import load_settings
from bets.kalshi.client import KalshiClient, UnwiredKalshiClient
from bets.models import Estimate, MarketQuote, Recommendation
from bets.store.repo import Repo
from bets.strategy.kelly import KellyStrategy

app = typer.Typer()
markets_app = typer.Typer()
rec_app = typer.Typer()
app.add_typer(markets_app, name="markets")
app.add_typer(rec_app, name="rec")


@app.callback()
def main() -> None:
    """bets — Kalshi market analysis and gated execution CLI."""


@app.command()
def env() -> None:
    """Print the resolved Kalshi environment and configured bankroll."""
    settings = load_settings()
    typer.echo(f"environment: {settings.env.value}")
    typer.echo(f"bankroll_cents: {settings.bankroll_cents}")


async def _fetch_quote(ticker: str, client: KalshiClient | None = None) -> MarketQuote:
    client = client or UnwiredKalshiClient()
    return await client.get_quote(ticker)


def _print_recommendation(rec: Recommendation) -> None:
    if not rec.actionable:
        typer.echo(f"no bet: {rec.rationale}")
        return
    typer.echo(
        f"{rec.side.value.upper()} {rec.contracts} @ {rec.price_cents}c (edge {rec.edge:+.3f})"
    )
    typer.echo(f"worst-case loss: {rec.worst_case_loss_cents}c")
    typer.echo(rec.rationale)


@rec_app.command("add")
def rec_add(
    market: str = typer.Option(..., "--market", help="Kalshi market ticker"),
    prob: float = typer.Option(
        ..., "--prob", help="Your probability estimate that the market resolves YES"
    ),
    yes_price: float | None = typer.Option(
        None,
        "--yes-price",
        help="Override the market YES price (0-1) and skip the network call",
    ),
) -> None:
    """Record a probability estimate and print the resulting recommendation."""
    settings = load_settings()
    estimate = Estimate(ticker=market, prob_yes=prob)

    if yes_price is not None:
        quote = MarketQuote(ticker=market, yes_price=yes_price)
    else:
        quote = asyncio.run(_fetch_quote(market))

    repo = Repo(settings.db_path)
    try:
        repo.record_estimate(estimate.ticker, estimate.prob_yes)
    finally:
        repo.close()

    strategy = KellyStrategy(
        kelly_fraction=settings.kelly_fraction, edge_threshold=settings.edge_threshold
    )
    rec = strategy.evaluate(quote, estimate, settings.bankroll_cents)
    _print_recommendation(rec)


@markets_app.command("quote")
def markets_quote(ticker: str) -> None:
    """Fetch a market's current quote via the Kalshi port."""
    quote = asyncio.run(_fetch_quote(ticker))
    typer.echo(f"{quote.ticker}: yes={quote.yes_price:.2f} no={quote.no_price:.2f}")


if __name__ == "__main__":
    app()
