"""Streamlit-cached data access layer.

Everything the UI reads goes through here, so caching lives in one place
instead of being sprinkled across the pages.
"""

import pandas as pd
import streamlit as st

from polymarket import fetch_price_history, load_markets


@st.cache_data(ttl=300)
def get_markets():
    """Snapshot of active markets, refreshed at most every five minutes."""
    df = pd.DataFrame(load_markets())
    end = pd.to_datetime(df["end_date"], errors="coerce", utc=True)
    df["days_left"] = (end - pd.Timestamp.now(tz="UTC")).dt.days
    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_history(token_id):
    """Roughly a month of hourly prices for one outcome token."""
    points = fetch_price_history(token_id, interval="1m", fidelity=60)

    if not points:
        return pd.DataFrame(columns=["ts", "price"])

    df = pd.DataFrame(points)
    df = df.rename(columns={"t": "ts", "p": "price"})
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    return df.dropna(subset=["price"]).sort_values("ts").reset_index(drop=True)