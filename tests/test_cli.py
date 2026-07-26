"""bets env prints the resolved environment and bankroll."""

from typer.testing import CliRunner

from bets.cli import app

runner = CliRunner()


def test_env_reports_demo_by_default(monkeypatch):
    monkeypatch.delenv("KALSHI_ENV", raising=False)
    result = runner.invoke(app, ["env"])
    assert result.exit_code == 0
    assert "environment: demo" in result.stdout
    assert "bankroll_cents:" in result.stdout


def test_env_reports_prod_when_explicitly_set(monkeypatch):
    monkeypatch.setenv("KALSHI_ENV", "prod")
    result = runner.invoke(app, ["env"])
    assert result.exit_code == 0
    assert "environment: prod" in result.stdout


def _db_path(tmp_path, monkeypatch):
    db_path = tmp_path / "bets.duckdb"
    monkeypatch.setenv("BETS_DB_PATH", str(db_path))
    return db_path


def test_rec_add_prints_recommendation_offline(tmp_path, monkeypatch):
    _db_path(tmp_path, monkeypatch)
    result = runner.invoke(
        app,
        [
            "rec",
            "add",
            "--market",
            "TICK",
            "--prob",
            "0.65",
            "--yes-price",
            "0.55",
        ],
    )
    assert result.exit_code == 0
    assert "YES" in result.stdout
    assert "101" in result.stdout
    assert "worst-case loss:" in result.stdout


def test_rec_add_no_bet_prints_reason(tmp_path, monkeypatch):
    _db_path(tmp_path, monkeypatch)
    result = runner.invoke(
        app,
        [
            "rec",
            "add",
            "--market",
            "TICK",
            "--prob",
            "0.52",
            "--yes-price",
            "0.50",
        ],
    )
    assert result.exit_code == 0
    assert "no bet" in result.stdout


def test_rec_add_persists_estimate(tmp_path, monkeypatch):
    from bets.store.repo import Repo

    db_path = _db_path(tmp_path, monkeypatch)
    runner.invoke(
        app,
        ["rec", "add", "--market", "TICK", "--prob", "0.65", "--yes-price", "0.55"],
    )
    repo = Repo(db_path)
    try:
        assert repo.latest_estimate("TICK") == 0.65
    finally:
        repo.close()


def test_markets_quote_invokes_unwired_kalshi_port(tmp_path, monkeypatch):
    _db_path(tmp_path, monkeypatch)
    result = runner.invoke(app, ["markets", "quote", "TICK"])
    assert result.exit_code != 0
    assert isinstance(result.exception, NotImplementedError)


def test_rec_add_without_yes_price_does_not_persist_on_unwired_quote(tmp_path, monkeypatch):
    from bets.store.repo import Repo

    db_path = _db_path(tmp_path, monkeypatch)
    result = runner.invoke(app, ["rec", "add", "--market", "TICK", "--prob", "0.65"])
    assert result.exit_code != 0
    assert isinstance(result.exception, NotImplementedError)

    repo = Repo(db_path)
    try:
        assert repo.latest_estimate("TICK") is None
    finally:
        repo.close()
