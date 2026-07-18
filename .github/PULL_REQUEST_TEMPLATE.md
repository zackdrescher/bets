<!-- Keep this short. Delete sections that don't apply. -->

## What & why

<!-- One or two lines: what changed and the reason. -->

## Docs sync

If this change alters **setup, commands, architecture, a safety gate, or a documented
convention**, the reflected docs must be updated in this same PR.

- [ ] `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, and any affected `docs/adr/` entry are updated — **or** this change touches none of the above.

The `docs-sync` CI check enforces this for doc-worthy paths. If it fails but docs truly
aren't needed, add the **`docs-not-needed`** label.

## Safety gates

The gates in `CLAUDE.md` are non-negotiable (demo default, `--dry-run` default, per-order
confirmation, spend caps, idempotency keys, kill-switch, append-only audit log, credential
isolation).

- [ ] This PR does **not** touch any safety gate, **or** it does and I've explained the change and sign-off below.

<!-- If a gate is touched, explain here: -->

## Checks

- [ ] `uv run pytest` passes (sizing + safety-gate tests green)
- [ ] `uv run ruff check .` passes
