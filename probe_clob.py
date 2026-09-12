"""One-off probe: check the real shape of the CLOB price-history response."""

import json

from polymarket import fetch_price_history, load_markets


def main():
    candidates = [m for m in load_markets() if m["token_ids"]]

    if not candidates:
        print("No market exposed `clobTokenIds` — the Gamma field name may differ.")
        return

    market = candidates[0]
    token_id = market["token_ids"][0]

    print(f"Market:   {market['question']}")
    print(f"Tokens:   {len(market['token_ids'])}")
    print(f"Using id: {token_id}\n")

    history = fetch_price_history(token_id)

    print(f"Points returned: {len(history)}")
    if history:
        print("\nFirst point:")
        print(json.dumps(history[0], indent=2))
        print("\nLast point:")
        print(json.dumps(history[-1], indent=2))


if __name__ == "__main__":
    main()