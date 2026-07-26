"""Environment gate must fail closed to demo."""

import pytest

from bets.config import KalshiEnv, Settings


def _settings(**kw):
    # Bypass .env file to test pure resolution logic.
    return Settings(_env_file=None, **kw)


def test_default_is_demo():
    assert _settings().env is KalshiEnv.DEMO


def test_unknown_env_fails_closed_to_demo():
    assert _settings(KALSHI_ENV="production-ish").env is KalshiEnv.DEMO
    assert _settings(KALSHI_ENV="").env is KalshiEnv.DEMO


def test_explicit_prod_opts_in():
    s = _settings(KALSHI_ENV="prod")
    assert s.env is KalshiEnv.PROD
    assert s.is_prod


def test_prod_is_case_insensitive_and_trimmed():
    assert _settings(KALSHI_ENV=" PROD ").env is KalshiEnv.PROD


def test_missing_credentials_raise():
    s = _settings(KALSHI_ENV="demo")
    with pytest.raises(RuntimeError):
        s.active_credentials()
