"""Configuration & environment gating.

Fail-closed: anything other than an explicit prod environment resolves to demo.
Credentials are read only from env / gitignored secret files, never hardcoded.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KalshiEnv(str, Enum):
    DEMO = "demo"
    PROD = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environment gate — defaults to demo; only the literal "prod" opts into production.
    kalshi_env: str = Field(default="demo", alias="KALSHI_ENV")

    kalshi_demo_api_key_id: str = Field(default="", alias="KALSHI_DEMO_API_KEY_ID")
    kalshi_demo_private_key_path: str = Field(
        default="", alias="KALSHI_DEMO_PRIVATE_KEY_PATH"
    )
    kalshi_prod_api_key_id: str = Field(default="", alias="KALSHI_PROD_API_KEY_ID")
    kalshi_prod_private_key_path: str = Field(
        default="", alias="KALSHI_PROD_PRIVATE_KEY_PATH"
    )

    db_path: str = Field(default="./bets.duckdb", alias="BETS_DB_PATH")

    bankroll_cents: int = Field(default=100_000, alias="BETS_BANKROLL_CENTS")
    kelly_fraction: float = Field(default=0.25, alias="BETS_KELLY_FRACTION")
    edge_threshold: float = Field(default=0.05, alias="BETS_EDGE_THRESHOLD")
    max_order_cents: int = Field(default=5_000, alias="BETS_MAX_ORDER_CENTS")
    max_daily_cents: int = Field(default=20_000, alias="BETS_MAX_DAILY_CENTS")

    @property
    def env(self) -> KalshiEnv:
        """Resolve the environment, failing closed to demo."""
        return KalshiEnv.PROD if self.kalshi_env.strip().lower() == "prod" else KalshiEnv.DEMO

    @property
    def is_prod(self) -> bool:
        return self.env is KalshiEnv.PROD

    def active_credentials(self) -> tuple[str, Path]:
        """Return (api_key_id, private_key_path) for the resolved environment.

        Raises if the active environment's credentials are not configured.
        """
        if self.is_prod:
            key_id, key_path = self.kalshi_prod_api_key_id, self.kalshi_prod_private_key_path
        else:
            key_id, key_path = self.kalshi_demo_api_key_id, self.kalshi_demo_private_key_path
        if not key_id or not key_path:
            raise RuntimeError(
                f"Missing Kalshi credentials for {self.env.value} environment. "
                "Set them in your .env / secret file (never commit keys)."
            )
        return key_id, Path(key_path)


def load_settings() -> Settings:
    return Settings()
