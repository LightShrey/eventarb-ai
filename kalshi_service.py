"""Kalshi market ingestion, with a deterministic hackathon fallback."""
from __future__ import annotations

import requests
from models import Market


DEMO_MARKETS = [
    Market("kalshi", "KXPRESELECT-26", "Will the Democratic nominee win the 2026 presidential election?", .54, .46, "2026-11-04", "Resolves YES if the Democratic Party nominee is certified as winner of the 2026 presidential election.", 128_000),
    Market("kalshi", "KXFEDCUT-DEC", "Will the Federal Reserve cut interest rates by December 2026?", .61, .39, "2026-12-31", "Resolves YES if the FOMC lowers its target federal funds rate at least once by December 31, 2026.", 84_500),
    Market("kalshi", "KXBTC-150K", "Will Bitcoin trade above $150,000 in 2026?", .43, .57, "2026-12-31", "Resolves YES if Coinbase BTC-USD last price reaches $150,000 before 2027.", 210_000),
]


def fetch_markets(limit: int = 40) -> tuple[list[Market], str]:
    """Try Kalshi's public endpoint; return demo data if its schema changes or is unavailable."""
    try:
        response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets", params={"limit": limit, "status": "open"}, timeout=7)
        response.raise_for_status()
        raw = response.json().get("markets", [])
        markets = []
        for item in raw:
            yes = item.get("yes_ask") or item.get("last_price")
            if yes is None:
                continue
            yes = float(yes) / 100 if float(yes) > 1 else float(yes)
            markets.append(Market("kalshi", str(item.get("ticker", "")), item.get("title") or item.get("subtitle", "Untitled Kalshi market"), yes, 1 - yes, str(item.get("close_time", "")), item.get("rules_primary") or item.get("rules", "Official Kalshi resolution rules."), float(item.get("liquidity", 0) or 0), f"https://kalshi.com/markets/{item.get('ticker', '')}"))
        if markets:
            return markets, f"Live Kalshi ({len(markets)} markets)"
    except (requests.RequestException, ValueError, TypeError):
        pass
    return DEMO_MARKETS, "Kalshi demo snapshot"
