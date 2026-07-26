"""DuckDB store — estimates, append-only audit log, daily spend, idempotency."""

from datetime import UTC, date, datetime, timedelta

import pytest

from bets.store import Repo
from bets.store import repo as repo_module


@pytest.fixture
def repo(tmp_path):
    r = Repo(tmp_path / "test.duckdb")
    yield r
    r.close()


def _submit(repo, monkeypatch, *, ticker="AAA", env="demo", stake=1_000, key="k1", ts=None):
    if ts is not None:
        monkeypatch.setattr(repo_module, "_now", lambda: ts)
    repo.append_audit(
        kind="submit",
        env=env,
        ticker=ticker,
        side="yes",
        contracts=10,
        price_cents=stake // 10,
        stake_cents=stake,
        idempotency_key=key,
    )


def test_record_and_retrieve_latest_estimate(repo):
    repo.record_estimate("AAA", 0.3)
    repo.record_estimate("AAA", 0.6)
    assert repo.latest_estimate("AAA") == 0.6


def test_latest_estimate_missing_ticker_returns_none(repo):
    assert repo.latest_estimate("NOPE") is None


def test_latest_estimate_is_per_ticker(repo):
    repo.record_estimate("AAA", 0.4)
    repo.record_estimate("BBB", 0.9)
    assert repo.latest_estimate("AAA") == 0.4
    assert repo.latest_estimate("BBB") == 0.9


def test_audit_log_has_no_update_or_delete_helpers(repo):
    public_methods = {name for name in dir(repo) if not name.startswith("_")}
    assert not any(m in public_methods for m in ("update_audit", "delete_audit"))


def test_audit_log_rejects_unknown_kind(repo):
    with pytest.raises(Exception):  # noqa: B017 - DuckDB raises its own constraint error type
        repo.append_audit(
            kind="bogus",
            env="demo",
            ticker="AAA",
            side="yes",
            contracts=10,
            price_cents=50,
            stake_cents=500,
            idempotency_key="k",
        )


def test_latest_estimate_breaks_ties_by_insertion_order(repo, monkeypatch):
    same_instant = datetime(2026, 1, 1, tzinfo=UTC)
    monkeypatch.setattr(repo_module, "_now", lambda: same_instant)
    repo.record_estimate("AAA", 0.2)
    repo.record_estimate("AAA", 0.7)
    assert repo.latest_estimate("AAA") == 0.7


def test_daily_spend_sums_submits_for_env_and_day(repo, monkeypatch):
    today = datetime.now(UTC)
    _submit(repo, monkeypatch, key="a", stake=1_000, ts=today)
    _submit(repo, monkeypatch, key="b", stake=2_500, ts=today)
    assert repo.spent_today_cents("demo") == 3_500


def test_daily_spend_excludes_other_envs(repo, monkeypatch):
    today = datetime.now(UTC)
    _submit(repo, monkeypatch, key="a", env="demo", stake=1_000, ts=today)
    _submit(repo, monkeypatch, key="b", env="prod", stake=5_000, ts=today)
    assert repo.spent_today_cents("demo") == 1_000
    assert repo.spent_today_cents("prod") == 5_000


def test_daily_spend_excludes_other_days(repo, monkeypatch):
    yesterday = datetime.now(UTC) - timedelta(days=1)
    _submit(repo, monkeypatch, key="a", stake=1_000, ts=yesterday)
    assert repo.spent_today_cents("demo") == 0


def test_daily_spend_can_be_queried_for_a_specific_day(repo, monkeypatch):
    target = date(2026, 1, 1)
    ts = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    _submit(repo, monkeypatch, key="a", stake=1_000, ts=ts)
    assert repo.spent_today_cents("demo", day=target) == 1_000


def test_daily_spend_with_no_activity_is_zero(repo):
    assert repo.spent_today_cents("demo") == 0


def test_idempotency_key_lookup(repo, monkeypatch):
    assert not repo.has_idempotency_key("dup-key")
    _submit(repo, monkeypatch, key="dup-key")
    assert repo.has_idempotency_key("dup-key")


def test_idempotency_key_scoped_to_submit_kind(repo):
    repo.append_audit(
        kind="fill",
        env="demo",
        ticker="AAA",
        side="yes",
        contracts=10,
        price_cents=50,
        stake_cents=500,
        idempotency_key="fill-only",
    )
    assert not repo.has_idempotency_key("fill-only")
