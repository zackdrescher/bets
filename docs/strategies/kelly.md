# Fractional Kelly sizing

How this project turns "I think the event is more/less likely than the market does" into a
position size. Read this before trusting the numbers.

## The setup

For a Kalshi YES contract:

- `p` — market price of YES, as a probability in `[0, 1]` (e.g. 55¢ ⇒ `p = 0.55`).
- `q` — **your** estimate that the event resolves YES, in `[0, 1]`.
- Buying 1 YES contract at price `p`:
  - **wins** `1 - p` if the event resolves YES,
  - **loses** `p` if it resolves NO.

So a YES bet is a wager at **net odds** `b = (1 - p) / p` (profit per unit staked if you win).

## Edge

```
edge = q - p
```

Positive edge ⇒ YES looks underpriced *by your estimate*. Negative edge ⇒ the NO side has the
edge (bet NO with `q_no = 1 - q`, `p_no = 1 - p`). We only act when `|edge|` clears a
configurable threshold (e.g. `0.05`) — small edges are mostly estimate noise.

## The Kelly fraction

The Kelly criterion picks the stake fraction of bankroll that maximizes long-run growth. For
a bet with win probability `q` and net odds `b`:

```
f* = (b·q - (1 - q)) / b
```

Substituting `b = (1 - p) / p` and simplifying for a binary contract gives the clean form:

```
f* = (q - p) / (1 - p)          # full-Kelly fraction of bankroll for a YES buy
```

Read it intuitively:
- The **numerator** is your edge `q - p`. No edge ⇒ zero stake.
- The **denominator** `1 - p` is your profit-if-right per contract. Cheaper contracts (small
  `p`, big potential payout) get sized up; expensive near-certain contracts get sized down.

If `f*` is negative, full Kelly says don't take this side (consider the opposite side).

## Why *fractional* Kelly

Full Kelly is growth-optimal **only if your probability `q` is exactly right**. It never is —
`q` is a subjective estimate. Full Kelly is also brutally volatile: large drawdowns are normal.

We scale the stake by a `kelly_fraction` (default `0.25`, "quarter Kelly"):

```
stake_fraction = kelly_fraction * f*
stake_dollars  = stake_fraction * bankroll
```

Quarter Kelly gives up a little theoretical growth for a large reduction in variance and in
sensitivity to `q` being wrong. This is the standard practitioner default.

## Guardrails applied on top

The raw Kelly number is never the final order. In order it is:

1. **Edge threshold** — skip if `|q - p| < threshold`.
2. **Fractional scaling** — multiply by `kelly_fraction`.
3. **Spend caps** — clamp to per-order and per-day dollar limits.
4. **Contract rounding** — convert to a whole number of contracts.
5. **Confirmation** — show side, size, price, and worst-case loss before any real submit.

## Worked example

Bankroll `$1,000`, `kelly_fraction = 0.25`, threshold `0.05`.

- Market: YES at `p = 0.55`. Your estimate `q = 0.65`.
- `edge = 0.65 - 0.55 = 0.10` ⇒ clears the threshold. ✅
- `f* = (0.65 - 0.55) / (1 - 0.55) = 0.10 / 0.45 ≈ 0.222` (full Kelly would stake ~22% of bankroll).
- `stake_fraction = 0.25 * 0.222 ≈ 0.0556` ⇒ **stake ≈ $55.6**.
- At 55¢/contract ⇒ ~**101 contracts** (before cap/rounding).
- Worst-case loss if it resolves NO ≈ the premium paid ≈ `$55.6`.

## Assumptions & limitations

- Assumes `q` is well-calibrated; a biased estimator makes Kelly systematically wrong. Track
  calibration over time.
- Ignores fees and bid/ask spread in the base formula — apply them before final sizing.
- Treats each bet independently; correlated positions can compound risk beyond single-bet Kelly.
- Binary-contract form only; multi-outcome markets need a different derivation.

## In code

Sizing lives in a pure function in `src/bets/strategy/kelly.py` — no I/O, fully unit-tested.
It implements the `Strategy` interface so alternative strategies (flat-stake, edge-threshold-only,
etc.) can be swapped in without touching the CLI or store.
