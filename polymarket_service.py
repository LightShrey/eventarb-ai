"""Polymarket Gamma API ingestion, with a deterministic hackathon fallback."""
from __future__ import annotations

import json
import requests
from models import Market


DEMO_MARKETS = [
    Market("polymarket", "PM-US-ELECTION", "Democratic candidate to win the 2026 US presidential election", .59, .41, "2026-11-04", "Resolves YES when a Democratic Party candidate is certified winner of the U.S. presidential election held in 2026.", 156_000),
    Market("polymarket", "PM-FED-CUT", "Fed rate cut before December 31, 2026", .37, .63, "2026-12-31", "Resolves YES if the Federal Reserve announces any decrease in the federal funds target range by December 31, 2026.", 93_000),
    Market("polymarket", "PM-BTC-150", "Bitcoin hits $150k by end of 2026", .60, .40, "2026-12-31", "Resolves YES if the Binance BTC/USDT spot price reaches 150,000 USD equivalent before January 1, 2027.", 176_000),
    Market("polymarket", "PM-FED-2027", "Fed rate cut before January 31, 2027", .42, .58, "2027-01-31", "Resolves YES if the Federal Reserve makes a target-rate cut by January 31, 2027.", 45_000),
]


def fetch_markets(limit: int = 40) -> tuple[list[Market], str]:
    try:
        response = requests.get("https://gamma-api.polymarket.com/markets", params={"active": "true", "closed": "false", "limit": limit}, timeout=7)
        response.raise_for_status()
        markets = []
        for item in response.json():
            prices = json.loads(item.get("outcomePrices", "[]"))
            if len(prices) < 2:
                continue
            yes, no = float(prices[0]), float(prices[1])
            markets.append(Market("polymarket", str(item.get("id", "")), item.get("question", "Untitled Polymarket market"), yes, no, str(item.get("endDate", "")), item.get("description", "Polymarket resolution rules."), float(item.get("liquidityNum", 0) or 0), f"https://polymarket.com/event/{item.get('slug', '')}"))
        if markets:
            return markets, f"Live Polymarket ({len(markets)} markets)"
    except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
        pass
    return DEMO_MARKETS, "Polymarket demo snapshot"
