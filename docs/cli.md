# CLI reference

All commands go through `uv run bets ...`. This is the full command surface as of
`src/bets/cli.py` — flags, defaults, and a short example for each. See the
[README quickstart](../README.md#quickstart) for the fastest path to a first command, and
`CLAUDE.md` for the safety gates referenced below.

## `bets env`

Show the resolved environment, DB path, and bankroll. No arguments.

```bash
uv run bets env
```

```
environment: demo
db: ./bets.duckdb
bankroll: $1,000.00
```

Useful as a sanity check before anything else — confirms you're pointed at demo (the default)
rather than prod.

## `bets markets quote <TICKER>`

Fetch a live market quote from Kalshi. Read-only; hits whatever environment `bets env` reports.

```bash
uv run bets markets quote KXFED-24DEC
```

```
KXFED-24DEC: YES 0.62 / NO 0.38
```

## `bets rec add`

Record your own probability estimate for a market and print the sizing recommendation
(edge + Kelly-derived size). Writes the estimate to the DuckDB store; does not touch Kalshi
orders.

| Flag | Required | Description |
|---|---|---|
| `--market`, `-m` | yes | Market ticker |
| `--prob`, `-p` | yes | Your P(YES), 0-1 |
| `--yes-price` | no | Override the market YES price (0-1) instead of fetching a live quote |

```bash
uv run bets rec add --market KXFED-24DEC --prob 0.65
```

```
edge 3.0% vs market 62% -- above threshold
-> YES 42 @ 65c = $27.30 (worst-case loss $27.30)
```

Use `--yes-price` to size against a hypothetical price without hitting the Kalshi API (e.g.
sanity-checking the Kelly math offline).

## `bets order place`

Compute a recommendation, run it through the safety gates, show a confirmation preview, and
optionally submit. This is the only command that can spend real money -- see the
[safety gates](../CLAUDE.md#non-negotiable-safety-rules) in `CLAUDE.md` for the full rationale.

| Flag | Required | Default | Description |
|---|---|---|---|
| `--market`, `-m` | yes | -- | Market ticker |
| `--prob`, `-p` | yes | -- | Your P(YES), 0-1 |
| `--yes-price` | no | fetched from Kalshi | Override the market YES price (0-1) |
| `--dry-run` / `--submit` | no | `--dry-run` | Preview only vs. actually submit |
| `--live` | no | off | Required (together with `KALSHI_ENV=prod`) to submit against prod |
| `--yes` | no | off | Skip the interactive "Submit this REAL order?" confirmation prompt |

Order of checks the command runs: build recommendation -> bail if not actionable ->
spend-cap check (per-order and per-day) -> print preview (side, size, price, worst-case loss) ->
prod gate (`KALSHI_ENV=prod` + `--live`, otherwise refused) -> dry-run short-circuit -> interactive
confirm (unless `--yes`) -> idempotent submit + audit log write.

**Preview (default -- nothing submitted):**

```bash
uv run bets order place --market KXFED-24DEC --prob 0.65
```

```
--- order preview ---
env:        demo
market:     KXFED-24DEC
side:       YES
contracts:  42
price:      65c
stake:      $27.30
worst-case loss: $27.30
[dry-run] no order submitted. Pass --submit to place.
```

**Real submit against demo, with interactive confirmation:**

```bash
uv run bets order place --market KXFED-24DEC --prob 0.65 --submit
```

**Real submit against prod** (requires the env var *and* the flag -- either alone is refused):

```bash
KALSHI_ENV=prod uv run bets order place --market KXFED-24DEC --prob 0.65 --submit --live
```

**Unattended submit** (e.g. scripted), skipping the confirmation prompt -- spend caps and the
prod gate still apply:

```bash
uv run bets order place --market KXFED-24DEC --prob 0.65 --submit --yes
```

## `bets order panic`

Kill-switch: cancels **all** resting orders in the current environment.

| Flag | Required | Default | Description |
|---|---|---|---|
| `--yes` | no | off | Skip the interactive confirmation prompt |

```bash
uv run bets order panic
```

```
Cancel ALL resting orders in demo? [y/N]: y
cancelled 3 order(s).
```

Scoped to whatever environment `bets env` currently resolves to -- cancel prod orders by running
with `KALSHI_ENV=prod` set, same as any other command.
