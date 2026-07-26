"""Typer app — CLI command wiring.

The Kalshi SDK is async; commands wrap async work with asyncio.run() so this
surface stays synchronous.
"""

from __future__ import annotations

import typer

from bets.config import load_settings

app = typer.Typer()


@app.callback()
def main() -> None:
    """bets — Kalshi market analysis and gated execution CLI."""


@app.command()
def env() -> None:
    """Print the resolved Kalshi environment and configured bankroll."""
    settings = load_settings()
    typer.echo(f"environment: {settings.env.value}")
    typer.echo(f"bankroll_cents: {settings.bankroll_cents}")


if __name__ == "__main__":
    app()
