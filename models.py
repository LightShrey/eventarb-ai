"""Shared domain types for EventArb AI."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Market:
    platform: str
    market_id: str
    title: str
    yes_price: float
    no_price: float
    close_time: str
    rules: str
    liquidity: float
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidatePair:
    kalshi: Market
    polymarket: Market
    keyword_score: float
    shared_terms: list[str]


@dataclass
class Verification:
    equivalence_score: int
    verdict: str
    critical_differences: list[str]
    short_reason: str
    checks: dict[str, str]
    provider: str = "heuristic"


@dataclass
class Opportunity:
    pair: CandidatePair
    side_a: str
    side_b: str
    gross_cost: float
    estimated_costs: float
    net_cost: float
    profit_per_dollar: float
    roi: float
    verification: Verification

    @property
    def label(self) -> str:
        return f"Buy Kalshi {self.side_a} + Polymarket {self.side_b}"
