# CONTEXT.md — domain & glossary

Canonical terms for this project. Keep this aligned with code; challenge drift.

## Domain glossary

| Term | Meaning in this project |
|------|-------------------------|
| **Market** | A single Kalshi binary contract identified by a ticker, resolving YES/NO. |
| **Event** | A real-world outcome a market is about (e.g. "CPI > 3.0% in Aug"). |
| **Price (`p`)** | Market price of a YES contract, 0–1 (i.e. cents/100). Implied probability. |
| **Estimate (`q`)** | The **user's** subjective probability the event resolves YES, 0–1. |
| **Edge** | `q - p`. Positive ⇒ YES looks underpriced; negative ⇒ NO side has edge. |
| **Strategy** | Pluggable rule mapping (market, estimate, bankroll) → a Recommendation. |
| **Recommendation** | Suggested `side`, `size`, `edge`, and human-readable `rationale`. Not an order. |
| **Order** | An instruction sent to Kalshi to buy/sell contracts. Real money unless demo. |
| **Fill** | An executed (partial or full) order, per Kalshi. Authoritative from the API. |
| **Position** | Net contracts currently held in a market. Authoritative from the Kalshi API. |
| **Bankroll** | Capital the sizing strategy is allowed to allocate from. Configurable. |
| **Kelly fraction** | Multiplier (default `0.25`) applied to full-Kelly stake to reduce variance. |
| **Dry-run** | Compute + display an order without submitting it. The **default** mode. |
| **Live** | Real order submission against `KALSHI_ENV=prod`. Requires explicit flags. |
| **Demo** | Kalshi's paper/sandbox environment. The **default** target. |

## Sides & pricing conventions

- A YES contract at price `p` pays `1 - p` profit if the event resolves YES, and loses `p`
  if it resolves NO. Worst-case loss per YES contract = `p` (the premium paid).
- To bet against an event, buy the NO side (`q_no = 1 - q`, `p_no = 1 - p`).
- Prices/sizes handled as integer **cents** / whole contracts internally to avoid float drift.

## Environments & authority

- **DuckDB** = system of record for estimates, recommendations, audit log.
- **Kalshi API** = authoritative for positions & fills (reconciled at read time).
- **Notion** = export/reporting only (planned). Never source of truth.

## Decision debt

- `TODO(decision-debt): choose external data-entry surface (Notion vs Google Sheets vs CLI-only); owner=user; trigger=when CLI probability entry feels heavy`
