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
