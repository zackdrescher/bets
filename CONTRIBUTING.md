# Contributing to bets

This project places **real-money orders** on Kalshi. Read the safety rules before touching
anything on the order path. When in doubt, stop and ask.

## Golden rule

The safety gates in [`CLAUDE.md`](CLAUDE.md) are non-negotiable. Never weaken, bypass, or make
optional: the demo default, `--dry-run` default, per-order confirmation, spend caps, idempotency
keys, the kill-switch, the append-only audit log, or credential isolation. A change that touches
any of them needs explicit sign-off in the PR description.

## Getting set up

This project uses [uv](https://docs.astral.sh/uv/) for a reproducible environment. The
interpreter is pinned in `.python-version` (3.11) and exact dependency versions are locked in
`uv.lock` — both are committed, so `uv sync` yields the same env for everyone.

```bash
# 1. Install uv once (macOS/Linux); see the uv docs for Homebrew/Windows/other installers
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create the env and install deps (incl. dev group) from the lockfile.
#    uv fetches the pinned Python automatically if you don't already have it.
uv sync

# 3. Configure credentials
cp .env.example .env          # then fill in Kalshi demo credentials
```

Changing dependencies? Edit `pyproject.toml`, then run `uv sync` (or `uv lock`) and commit the
updated `uv.lock` alongside it. Never hand-edit `uv.lock`.

- Credentials load only from env vars or a gitignored secret file. Never commit keys.
  `secrets/` and `*.pem` are gitignored; keep demo and prod key sets separate.
- Everything defaults to Kalshi **demo**. Production requires `KALSHI_ENV=prod` **and** `--live`.

## Running checks

```bash
uv run pytest                 # tests — sizing + safety-gate tests must stay green
uv run ruff check .           # lint
uv run ruff format .          # format
```

Tests for the Kelly function and the safety gates are **required**, not optional. A PR that
changes money math or a gate without a corresponding test won't be accepted.

## Keep docs in sync

When a change alters setup, commands, architecture, a safety gate, or a documented convention,
update the reflected docs (`README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `docs/`) in the **same**
PR. The `docs-sync` GitHub Action enforces this: if a doc-worthy path changes with no doc
update, the check fails. If docs genuinely aren't needed, add the **`docs-not-needed`** label to
the PR. The watched paths live in [`.github/workflows/docs-sync.yml`](.github/workflows/docs-sync.yml).

## How work flows here

Work is tracked as **GitHub issues** (see [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md))
and specced/sliced with the project's agent skills:

1. A **spec** issue captures the plan (problem, user stories, decisions).
2. `/to-tickets` splits it into **tracer-bullet tickets**, each a vertical slice with native
   **blocking edges**. Tickets carry the `ready-for-agent` label.
3. Pick a ticket whose blockers are all closed (the *frontier*), implement it on its own branch
   in a fresh context, then open a PR. Clear context between tickets.

Each ticket should stay small enough to finish in one focused session and be verifiable on its own.

## Coding conventions

- **Stack:** uv · Typer · Pydantic · DuckDB · pytest · ruff · `kalshi-python-async`.
- **Money math is pure.** Sizing/risk functions take values in and return values out — no I/O,
  no network, no DB. This keeps them testable and swappable (see the `Strategy` interface).
- **Money as integer cents** and whole contracts internally. Avoid float drift on prices/sizes.
- **Async at the edge.** The Kalshi SDK is async; wrap calls with `asyncio.run()` at the CLI
  command boundary so the CLI surface stays synchronous.
- **Kalshi behind the port.** All SDK calls live behind the client port; nothing else imports
  the SDK directly.
- **Respect the ADRs.** Architecture decisions live in [`docs/adr/`](docs/adr/); domain terms in
  [`CONTEXT.md`](CONTEXT.md). Use that vocabulary in code and tickets.
- **Smallest safe diff.** Prefer root-cause fixes in the shared path over caller-by-caller
  patches. Deferred decisions get a `TODO(decision-debt): ...; owner=...; trigger=...` marker.

## Commits & branches

- Branch off `main`; don't commit directly to it.
- Keep commits scoped and messages descriptive (what changed and why).
- Never commit secrets, real keys, or a populated `.env`.

## The audit log is sacred

The DuckDB audit log is **append-only**. Code may insert submit/fill rows; it must never update
or delete them. Treat any change that could mutate history as a red flag.
