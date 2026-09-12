"""Fetch active Polymarket markets from the Gamma API and print the top ones by volume."""

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


def fetch_markets(limit=100):
    """Return a list of currently active, non-closed markets."""
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

    yes_price = to_float(prices[0]) if prices else 0.0

    return {
        "question": market.get("question", "—"),
        "outcomes": outcomes,
        "yes_price": yes_price,
        "volume": to_float(market.get("volumeNum") or market.get("volume")),
        "liquidity": to_float(market.get("liquidityNum") or market.get("liquidity")),
        "end_date": (market.get("endDate") or "")[:10],
    }


def main():
    markets = [summarize(m) for m in fetch_markets()]
    markets.sort(key=lambda m: m["volume"], reverse=True)

    print(f"Fetched {len(markets)} active markets. Top 10 by volume:\n")
    for i, market in enumerate(markets[:10], start=1):
        print(f"{i:>2}. {market['question'][:70]}")
        print(
            f"    YES: {market['yes_price']:.0%}"
            f" | volume: ${market['volume']:,.0f}"
            f" | ends: {market['end_date'] or 'n/a'}"
        )


if __name__ == "__main__":
    main()