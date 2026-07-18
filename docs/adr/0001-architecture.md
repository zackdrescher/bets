# ADR 0001 — Initial architecture

- **Status:** Accepted
- **Date:** 2026-07-18
- **Owner:** user

## Context

We want tooling to work with Kalshi event markets: analyze markets, record the user's own
event probability estimates, manage open positions, and place orders. Real money can be at
stake, so safety and reversibility dominate the design. The user prefers Python and a CLI as
the primary surface, with lightweight external data-entry surfaces (Notion / Google Sheets)
as a possible later addition.

## Decisions

### D1 — Posture: decision-support with supported, gated execution
Analysis is always available and spends nothing. Order execution is supported but
human-in-the-loop: every real order requires explicit per-order confirmation. Execution
ships in v1 **only** with its full guard set (see D6); it is never a silent/automated path.

### D2 — Sizing: fractional Kelly behind a swappable Strategy interface
Position sizing uses fractional Kelly (default `0.25`) gated by an edge threshold. Sizing
math lives in a **pure, unit-tested** function with no I/O. A `Strategy` interface
(`evaluate(market, estimate, bankroll) -> Recommendation`) allows swapping/adding strategies
over time. Kelly is implementation #1. See `docs/strategies/kelly.md`.

### D3 — System of record: DuckDB local file
DuckDB stores probability estimates, recommendations, and the append-only audit log. It is
an OLAP/single-writer store — acceptable for a single-user CLI. Bet/fill writes are
serialized; the DB file is backed up.
> `TODO(decision-debt): revisit store if usage becomes multi-writer/concurrent; owner=user; trigger=second concurrent client or web surface`

### D4 — Kalshi API authoritative for positions & fills
Live positions and fills are read from Kalshi at read time, not trusted from local cache.
Local state is reconciled against the API.

### D5 — Environment gating: fail-closed to demo
Default target is Kalshi's demo/paper environment. Production requires `KALSHI_ENV=prod`
**and** an explicit `--live` flag. Credentials load only from env vars or a gitignored secret
file, with separate demo and prod key sets; secrets are never committed or logged.

### D6 — Execution guards (mandatory for any real order)
1. `--dry-run` is the default; real submit is opt-in.
2. Prod requires `KALSHI_ENV=prod` + `--live`.
3. Per-order confirmation shows side, size, price, worst-case loss.
4. Per-order and per-day spend caps checked before submit.
5. Idempotency key on every order.
6. Kill-switch (`order panic`) cancels resting orders.
7. Append-only audit log for every submit and fill.

### D7 — Notion/Sheets are export surfaces only (deferred)
External surfaces are optional export/reporting adapters behind an interface, never the
system of record.
> `TODO(decision-debt): choose external data-entry surface (Notion vs Sheets vs CLI-only); owner=user; trigger=when CLI probability entry feels heavy`

### D8 — Stack
uv, Typer, Pydantic, DuckDB, pytest, ruff, and `kalshi-python-async`. The SDK is async;
wrap with `asyncio.run()` at the CLI command boundary to keep the CLI synchronous.

## Consequences

- **Positive:** capital-at-risk paths are guarded and reversible-by-default; core value
  (edge + sizing) is testable without spending money; strategies are swappable.
- **Negative / risks:** live execution surface exists in v1 (highest risk area — mitigated by
  D6 guards); DuckDB single-writer constraint; credential handling correctness is on the user.

## Alternatives considered

- **Notion/Sheets as system of record** — rejected: inherits sync conflict + availability
  coupling to real-money decisions.
- **Full automated execution engine** — rejected for v1: requires trusting more automation
  before the recommendation logic is validated.
- **Flat-stake sizing** — rejected as default: leaves bankroll-aware edge on the table
  (kept easy to add as an alternative Strategy).

## v1 scope

Full loop including gated `place`, with all D6 guards as acceptance criteria.
