# CLAUDE.md — bets

Guidance for AI assistants (and humans) working in this repository.

## What this is

CLI tooling to analyze [Kalshi](https://kalshi.com) event markets, record the user's own
probability estimates, compute edge + position size via a swappable strategy, and — behind
hard safety gates — place real orders. **Real money is at stake.** Treat order execution as
an irreversible, data-loss-class action.

## Non-negotiable safety rules

Never weaken, bypass, or make optional any of these:

1. **Default to Kalshi demo.** Production requires `KALSHI_ENV=prod` **and** an explicit
   `--live` flag. Anything unset ⇒ demo.
2. **`--dry-run` is the default** for order commands; a real submit is opt-in.
3. **Per-order confirmation** must show side, size, price, and worst-case loss before submit.
4. **Spend caps** (per-order and per-day) are checked before every submit.
5. **Idempotency key** on every order — no path may double-submit on retry/crash.
6. **Kill-switch** (`order panic`) must always be able to cancel resting orders.
7. **Append-only audit log** in DuckDB for every submit and fill. Never mutate/delete rows.
8. **Credentials** load only from env vars or a gitignored secret file. Never commit keys;
   never log secrets. Keep demo and prod key sets separate.

If a change would touch any of the above, stop and confirm with the user first.

## Architecture (see docs/adr/0001-architecture.md)

- **System of record:** DuckDB local file — estimates, recommendations, audit log.
- **Authoritative for positions/fills:** the Kalshi API, reconciled at read time.
- **Notion:** export surface only (planned). Never the system of record.
- **Strategy** is a swappable interface (`evaluate(...) -> Recommendation`). Fractional
  Kelly is implementation #1; keep sizing math in a **pure, unit-tested** function.
- Kalshi SDK is async; wrap with `asyncio.run()` at the CLI command boundary so the CLI
  surface stays synchronous.

## Layout

```
src/bets/
  cli.py            # Typer app, command wiring
  config.py         # env/credential loading, KALSHI_ENV gate
  strategy/         # Strategy interface + kelly.py (pure sizing fns)
  store/            # DuckDB repository, schema, audit log
  kalshi/           # client wrapper around kalshi-python-async
docs/adr/           # architecture decision records
docs/strategies/    # written explainers (kelly.md)
tests/              # pytest — sizing + safety-gate tests are first-class
```

## Stack & conventions

- uv · Typer · Pydantic · DuckDB · pytest · ruff · `kalshi-python-async`
- Pure functions for money math; no I/O inside strategy code.
- Money as integer cents where possible; avoid float drift on prices/sizes.
- Tests for the Kelly function and the safety gates are **required**, not optional.

## Working style

- Evidence-first, minimal-change, smallest safe diff.
- Ask before scope grows beyond a bounded task; the user owns product/architecture decisions.
- Deferred decisions get a `TODO(decision-debt): ...; owner=...; trigger=...` marker.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (zackdrescher/bets), via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
