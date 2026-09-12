"""Thin client for the public Polymarket Gamma API."""

import json

import httpx

GAMMA_API = "https://gamma-api.polymarket.com/markets"


def to_float(value, default=0.0):
    """Gamma returns numbers as strings sometimes — normalize them."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_json_field(value):
    """Fields like `outcomes` and `outcomePrices` arrive as JSON-encoded strings."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value or []


def fetch_markets(limit=200):
    """Return raw payloads for currently active, non-closed markets."""
    params = {
        "active": "true",
        "closed": "false",
        "limit": limit,
        "order": "volumeNum",
        "ascending": "false",
    }
    response = httpx.get(GAMMA_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def summarize(market):
    """Reduce a raw market payload to the handful of fields we care about."""
    outcomes = parse_json_field(market.get("outcomes"))
    prices = parse_json_field(market.get("outcomePrices"))

    return {
        "question": market.get("question") or "—",
        "outcomes": ", ".join(str(o) for o in outcomes) or "—",
        "probability": to_float(prices[0]) if prices else 0.0,
        "volume": to_float(market.get("volumeNum") or market.get("volume")),
        "liquidity": to_float(market.get("liquidityNum") or market.get("liquidity")),
        "end_date": (market.get("endDate") or "")[:10],
        "slug": market.get("slug") or "",
    }


def load_markets(limit=200):
    """Fetch and simplify markets, sorted by volume descending."""
    markets = [summarize(m) for m in fetch_markets(limit)]
    markets.sort(key=lambda m: m["volume"], reverse=True)
    return markets