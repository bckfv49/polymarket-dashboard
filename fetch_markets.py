"""CLI helper: print the top Polymarket markets by volume."""

from polymarket import load_markets


def main():
    markets = load_markets()

    print(f"Fetched {len(markets)} active markets. Top 10 by volume:\n")
    for i, market in enumerate(markets[:10], start=1):
        print(f"{i:>2}. {market['question'][:70]}")
        print(
            f"    YES: {market['probability']:.0%}"
            f" | volume: ${market['volume']:,.0f}"
            f" | ends: {market['end_date'] or 'n/a'}"
        )


if __name__ == "__main__":
    main()