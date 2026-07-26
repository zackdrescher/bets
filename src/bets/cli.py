"""Typer CLI. Async SDK calls are wrapped with asyncio.run at this boundary.

Safety gates enforced here:
  - default to demo (config fail-closed)
  - --dry-run is the default for `order place`
  - prod requires KALSHI_ENV=prod AND --live
  - per-order confirmation shows worst-case loss
  - spend caps checked before submit
  - idempotency key per order
  - every submit/fill appended to the audit log
"""

from __future__ import annotations

import asyncio
import uuid

import typer

from bets.config import load_settings
from bets.kalshi import KalshiClient
from bets.models import Estimate, MarketQuote
from bets.risk import check_spend_caps
from bets.store import Repo
from bets.strategy import KellyStrategy, StrategyConfig

app = typer.Typer(help="Kalshi decision-support & gated execution.", no_args_is_help=True)
markets_app = typer.Typer(help="Market analysis (read-only).")
rec_app = typer.Typer(help="Record estimates & compute recommendations.")
order_app = typer.Typer(help="Order execution (gated).")
app.add_typer(markets_app, name="markets")
app.add_typer(rec_app, name="rec")
app.add_typer(order_app, name="order")


def _strategy(settings) -> KellyStrategy:
    return KellyStrategy(
        StrategyConfig(
            kelly_fraction=settings.kelly_fraction,
            edge_threshold=settings.edge_threshold,
        )
    )


@app.command()
def env() -> None:
    """Show the resolved environment (fail-closed to demo)."""
    s = load_settings()
    typer.echo(f"environment: {s.env.value}")
    typer.echo(f"db: {s.db_path}")
    typer.echo(f"bankroll: ${s.bankroll_cents / 100:,.2f}")


@markets_app.command("quote")
def markets_quote(ticker: str) -> None:
    """Fetch a market quote from Kalshi (read-only)."""
    s = load_settings()
    client = KalshiClient(s)
    quote = asyncio.run(client.get_quote(ticker))
    typer.echo(f"{quote.ticker}: YES {quote.yes_price:.2f} / NO {quote.no_price:.2f}")


@rec_app.command("add")
def rec_add(
    ticker: str = typer.Option(..., "--market", "-m"),
    prob: float = typer.Option(..., "--prob", "-p", help="Your P(YES), 0-1"),
    yes_price: float | None = typer.Option(
        None, "--yes-price", help="Override market YES price 0-1 (else fetched)"
    ),
) -> None:
    """Record an estimate and show the sizing recommendation."""
    s = load_settings()
    repo = Repo(s.db_path)
    repo.record_estimate(ticker, prob)

    if yes_price is None:
        quote = asyncio.run(KalshiClient(s).get_quote(ticker))
    else:
        quote = MarketQuote(ticker=ticker, yes_price=yes_price)

    rec = _strategy(s).evaluate(quote, Estimate(ticker=ticker, prob_yes=prob), s.bankroll_cents)
    typer.echo(rec.rationale)
    if rec.actionable:
        typer.echo(
            f"-> {rec.side.value.upper()} {rec.contracts} @ {rec.price_cents}c "
            f"= ${rec.stake_cents / 100:.2f} "
            f"(worst-case loss ${rec.worst_case_loss_cents / 100:.2f})"
        )
    repo.close()


@order_app.command("place")
def order_place(
    ticker: str = typer.Option(..., "--market", "-m"),
    prob: float = typer.Option(..., "--prob", "-p", help="Your P(YES), 0-1"),
    yes_price: float | None = typer.Option(None, "--yes-price"),
    dry_run: bool = typer.Option(True, "--dry-run/--submit", help="Default: dry-run"),
    live: bool = typer.Option(False, "--live", help="Required (with KALSHI_ENV=prod) for prod"),
    yes: bool = typer.Option(False, "--yes", help="Skip interactive confirmation prompt"),
) -> None:
    """Compute, gate, confirm, and (optionally) submit an order."""
    s = load_settings()
    repo = Repo(s.db_path)

    if yes_price is None:
        quote = asyncio.run(KalshiClient(s).get_quote(ticker))
    else:
        quote = MarketQuote(ticker=ticker, yes_price=yes_price)

    rec = _strategy(s).evaluate(quote, Estimate(ticker=ticker, prob_yes=prob), s.bankroll_cents)
    if not rec.actionable:
        typer.echo(f"No actionable bet: {rec.rationale}")
        repo.close()
        raise typer.Exit(0)

    # --- spend caps ---
    cap = check_spend_caps(
        rec.stake_cents,
        max_order_cents=s.max_order_cents,
        max_daily_cents=s.max_daily_cents,
        spent_today_cents=repo.spent_today_cents(s.env.value),
    )
    if not cap.approved:
        typer.echo(f"BLOCKED by spend caps: {cap.reason}")
        repo.close()
        raise typer.Exit(1)

    # --- confirmation summary ---
    typer.echo("--- order preview ---")
    typer.echo(f"env:        {s.env.value}")
    typer.echo(f"market:     {rec.ticker}")
    typer.echo(f"side:       {rec.side.value.upper()}")
    typer.echo(f"contracts:  {rec.contracts}")
    typer.echo(f"price:      {rec.price_cents}c")
    typer.echo(f"stake:      ${rec.stake_cents / 100:.2f}")
    typer.echo(f"worst-case loss: ${rec.worst_case_loss_cents / 100:.2f}")

    # --- prod gate ---
    if s.is_prod and not live:
        typer.echo("REFUSED: prod environment requires --live. (fail-closed)")
        repo.close()
        raise typer.Exit(1)

    if dry_run:
        typer.echo("[dry-run] no order submitted. Pass --submit to place.")
        repo.close()
        raise typer.Exit(0)

    if not yes and not typer.confirm("Submit this REAL order?"):
        typer.echo("cancelled.")
        repo.close()
        raise typer.Exit(0)

    # --- idempotent submit + audit ---
    key = uuid.uuid4().hex
    if repo.has_idempotency_key(key):  # near-impossible collision; guard anyway
        typer.echo("duplicate idempotency key; aborting.")
        repo.close()
        raise typer.Exit(1)

    client = KalshiClient(s)
    result = asyncio.run(
        client.place_order(
            ticker=rec.ticker,
            side=rec.side,
            contracts=rec.contracts,
            price_cents=rec.price_cents,
            idempotency_key=key,
        )
    )
    repo.append_audit(
        kind="submit" if result.accepted else "reject",
        env=s.env.value,
        ticker=rec.ticker,
        side=rec.side.value,
        contracts=rec.contracts,
        price_cents=rec.price_cents,
        stake_cents=rec.stake_cents,
        idempotency_key=key,
        detail=result.detail,
    )
    typer.echo(f"{'SUBMITTED' if result.accepted else 'REJECTED'}: {result.detail}")
    repo.close()


@order_app.command("panic")
def order_panic(
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation"),
) -> None:
    """Kill-switch: cancel all resting orders."""
    s = load_settings()
    if not yes and not typer.confirm(f"Cancel ALL resting orders in {s.env.value}?"):
        typer.echo("cancelled.")
        raise typer.Exit(0)
    count = asyncio.run(KalshiClient(s).cancel_all())
    typer.echo(f"cancelled {count} order(s).")


if __name__ == "__main__":
    app()
