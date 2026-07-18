"""Core domain models. See CONTEXT.md for canonical term definitions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Side(str, Enum):
    YES = "yes"
    NO = "no"


class MarketQuote(BaseModel):
    """A snapshot of a Kalshi market relevant to sizing."""

    ticker: str
    yes_price: float = Field(ge=0.0, le=1.0, description="YES price as probability 0-1")

    @property
    def no_price(self) -> float:
        return 1.0 - self.yes_price


class Estimate(BaseModel):
    """The user's subjective probability that the event resolves YES."""

    ticker: str
    prob_yes: float = Field(ge=0.0, le=1.0)

    @field_validator("prob_yes")
    @classmethod
    def _not_degenerate(cls, v: float) -> float:
        if v in (0.0, 1.0):
            # Allowed, but degenerate estimates make Kelly explode; caller should be careful.
            return v
        return v


class Recommendation(BaseModel):
    """Output of a Strategy. Not an order — just advice."""

    ticker: str
    side: Side
    edge: float
    contracts: int = Field(ge=0)
    stake_cents: int = Field(ge=0)
    price_cents: int = Field(ge=0, le=100)
    rationale: str

    @property
    def worst_case_loss_cents(self) -> int:
        """Premium at risk = price paid per contract * contracts."""
        return self.price_cents * self.contracts

    @property
    def actionable(self) -> bool:
        return self.contracts > 0
