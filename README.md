# bets

Decision-support and (gated) execution tooling for [Kalshi](https://kalshi.com) event markets.

You record your own probability estimates for events; the tool computes your edge
versus the market, suggests a position size via a swappable strategy (fractional
Kelly by default), and — behind explicit safety gates — can place real orders.

## Core loop

```
record probability  ->  fetch market + positions (Kalshi)  ->  compute edge + size (Strategy)
      ->  review recommendation  ->  confirm  ->  place order (gated)  ->  audit log
```

## Posture

- **Decision-support first.** Analysis is always available; nothing spends money on its own.
- **Human-in-the-loop.** Every real order requires explicit per-order confirmation.
- **Fail-closed.** Defaults to Kalshi's **demo** environment. Production requires an
  explicit environment switch *and* a `--live` flag.

## System of record

- **DuckDB** (local file) owns probability estimates, recommendations, and the append-only
  order/fill audit log.
- The **Kalshi API is authoritative** for current positions and fills — reconciled at read time.
- **Notion** (planned) is an *export* surface only, never the system of record.

## Safety gates (mandatory for order execution)

1. `--dry-run` is the **default**; a real submit needs an explicit flag.
2. Production orders require `KALSHI_ENV=prod` **and** `--live` (otherwise demo).
3. Per-order confirmation shows side, size, price, and worst-case loss.
4. Per-order and per-day **spend caps**, enforced before submit.
5. Every order carries an **idempotency key** (no double-submit on retry/crash).
6. **Kill-switch** command cancels all resting orders.
7. Every submit/fill is written to an **append-only audit log**.

## Stack

- [uv](https://docs.astral.sh/uv/) — env & dependency management
- [Typer](https://typer.tiangolo.com/) — CLI
- [Pydantic](https://docs.pydantic.dev/) — models & validation
- [DuckDB](https://duckdb.org/) — local store
- [`kalshi-python-async`](https://pypi.org/project/kalshi-python-async/) — Kalshi SDK
- pytest · ruff

## Status

Early scaffolding. See [`docs/adr/0001-architecture.md`](docs/adr/0001-architecture.md)
for the design and [`docs/strategies/kelly.md`](docs/strategies/kelly.md) for the sizing model.

## Quickstart

```bash
uv sync
cp .env.example .env          # fill in Kalshi demo credentials
uv run bets markets list      # read-only, hits demo by default
uv run bets rec add --market <TICKER> --prob 0.65   # record an estimate + see edge/size
uv run bets order place --market <TICKER> --dry-run # preview an order (default)
```

> Nothing places a real order unless you pass the explicit live/submit flags. See safety gates above.

## Disclaimer

This software can place real-money orders on prediction markets. It ships with no
warranty and makes no guarantee of profit. You are solely responsible for your trades,
your credentials, and compliance with Kalshi's terms and applicable law.
