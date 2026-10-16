"""Cross-venue binary-contract arbitrage calculations."""
from __future__ import annotations

from models import CandidatePair, Opportunity, Verification


def calculate(pair: CandidatePair, verification: Verification, fees: float = .01, slippage: float = .005) -> list[Opportunity]:
    options = [("YES", "NO", pair.kalshi.yes_price + pair.polymarket.no_price), ("NO", "YES", pair.kalshi.no_price + pair.polymarket.yes_price)]
    results = []
    for side_a, side_b, gross_cost in options:
        costs = fees + slippage
        net_cost = gross_cost + costs
        profit = 1 - net_cost
        results.append(Opportunity(pair, side_a, side_b, gross_cost, costs, net_cost, profit, (profit / net_cost * 100) if net_cost else 0, verification))
    return results


def rank(opportunities: list[Opportunity], min_equivalence: int = 90, min_roi: float = 0) -> list[Opportunity]:
    safe = [item for item in opportunities if item.verification.equivalence_score >= min_equivalence and item.roi > min_roi]
    return sorted(safe, key=lambda item: (item.roi, item.verification.equivalence_score, min(item.pair.kalshi.liquidity, item.pair.polymarket.liquidity)), reverse=True)
