"""DuckDB repository. Single-writer; the audit log is append-only.

Design rule: never UPDATE or DELETE audit rows. Positions/fills are authoritative from the
Kalshi API, not from this store — this store records *our* intent and observed outcomes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

_SCHEMA = """
CREATE TABLE IF NOT EXISTS estimates (
    id BIGINT DEFAULT nextval('seq_estimates'),
    ticker VARCHAR NOT NULL,
    prob_yes DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT DEFAULT nextval('seq_audit'),
    ts TIMESTAMP NOT NULL,
    kind VARCHAR NOT NULL,        -- 'submit' | 'fill' | 'cancel' | 'reject'
    env VARCHAR NOT NULL,         -- 'demo' | 'prod'
    ticker VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    contracts INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    stake_cents INTEGER NOT NULL,
    idempotency_key VARCHAR NOT NULL,
    detail VARCHAR
);
"""


class Repo:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._con = duckdb.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self._con.execute("CREATE SEQUENCE IF NOT EXISTS seq_estimates START 1;")
        self._con.execute("CREATE SEQUENCE IF NOT EXISTS seq_audit START 1;")
        self._con.execute(_SCHEMA)

    # --- estimates -------------------------------------------------------
    def record_estimate(self, ticker: str, prob_yes: float) -> None:
        self._con.execute(
            "INSERT INTO estimates (ticker, prob_yes, created_at) VALUES (?, ?, ?)",
            [ticker, prob_yes, _now()],
        )

    def latest_estimate(self, ticker: str) -> float | None:
        row = self._con.execute(
            "SELECT prob_yes FROM estimates WHERE ticker = ? "
            "ORDER BY created_at DESC LIMIT 1",
            [ticker],
        ).fetchone()
        return row[0] if row else None

    # --- audit log (append-only) ----------------------------------------
    def append_audit(
        self,
        *,
        kind: str,
        env: str,
        ticker: str,
        side: str,
        contracts: int,
        price_cents: int,
        stake_cents: int,
        idempotency_key: str,
        detail: str = "",
    ) -> None:
        self._con.execute(
            "INSERT INTO audit_log (ts, kind, env, ticker, side, contracts, "
            "price_cents, stake_cents, idempotency_key, detail) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                _now(), kind, env, ticker, side, contracts,
                price_cents, stake_cents, idempotency_key, detail,
            ],
        )

    def has_idempotency_key(self, idempotency_key: str) -> bool:
        row = self._con.execute(
            "SELECT 1 FROM audit_log WHERE idempotency_key = ? AND kind = 'submit' LIMIT 1",
            [idempotency_key],
        ).fetchone()
        return row is not None

    def spent_today_cents(self, env: str, day: date | None = None) -> int:
        day = day or datetime.now(timezone.utc).date()
        row = self._con.execute(
            "SELECT COALESCE(SUM(stake_cents), 0) FROM audit_log "
            "WHERE kind = 'submit' AND env = ? AND CAST(ts AS DATE) = ?",
            [env, day],
        ).fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._con.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)
