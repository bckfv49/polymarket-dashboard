"""Detail page — one market, one month of hourly prices."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import get_history, get_markets
from theme import (
    BASELINE, BLUE, BLUE_WASH, GRID, INK, INK_MUTED, MONO, PANEL,
    apply_chrome, compact_money, inject_css, shorten, term_header,
)

st.set_page_config(page_title="Market detail", page_icon="◧", layout="wide")
inject_css()
term_header("CLOB API · PRICE HISTORY")

markets = get_markets()
tradable = markets[markets["token_ids"].apply(bool)].reset_index(drop=True)

if tradable.empty:
    st.error("No market exposed CLOB token ids.")
    st.stop()

# --- Market picker (remembers the choice made on the overview page) --------
questions = tradable["question"].tolist()
preselected = st.session_state.get("selected_question")
default_index = questions.index(preselected) if preselected in questions else 0

choice = st.selectbox(
    "Market",
    options=range(len(questions)),
    index=default_index,
    format_func=lambda i: shorten(questions[i], 100),
)
market = tradable.loc[choice]
st.session_state["selected_question"] = market["question"]

history = get_history(market["token_ids"][0])

if history.empty:
    st.warning(
        "CLOB returned no price history for this market. "
        "Newly listed markets often have none yet — try another one."
    )
    st.stop()

# --- Derived stats ---------------------------------------------------------
latest = history.iloc[-1]
now = history["ts"].max()


def change_since(hours):
    """Percentage-point move over the last `hours`, or None if data is short."""
    window = history[history["ts"] <= now - pd.Timedelta(hours=hours)]
    if window.empty:
        return None
    return (latest["price"] - window.iloc[-1]["price"]) * 100


delta_24h = change_since(24)
delta_7d = change_since(24 * 7)

# --- Hero figure — exactly one per view ------------------------------------
st.markdown(
    f"""
    <div class="hero-label">Current YES price</div>
    <div class="hero-value">{latest['price']:.0%}</div>
    <div class="hero-question">{market['question']}</div>
    """,
    unsafe_allow_html=True,
)

st.write("")

s1, s2, s3, s4, s5 = st.columns(5)
s1.metric(
    "24h change",
    "—" if delta_24h is None else f"{delta_24h:+.1f} pp",
    delta_color="off",
)
s2.metric(
    "7d change",
    "—" if delta_7d is None else f"{delta_7d:+.1f} pp",
    delta_color="off",
)
s3.metric("Period high", f"{history['price'].max():.0%}")
s4.metric("Period low", f"{history['price'].min():.0%}")
s5.metric("Volume", compact_money(market["volume"]))

# --- Range control ---------------------------------------------------------
st.subheader("Price history")

ranges = {"24H": 1, "7D": 7, "30D": 30}
picked = st.radio(
    "Range", list(ranges), index=2, horizontal=True, label_visibility="collapsed"
)
window = history[history["ts"] >= now - pd.Timedelta(days=ranges[picked])]

if len(window) < 2:
    st.info(f"Not enough points in the last {picked.lower()} — showing everything.")
    window = history

# --- The line chart --------------------------------------------------------
price_fig = go.Figure(
    go.Scatter(
        x=window["ts"],
        y=window["price"] * 100,
        mode="lines",
        line=dict(color=BLUE, width=2, shape="spline", smoothing=0.3),
        fill="tozeroy",
        fillcolor=BLUE_WASH,
        hovertemplate="%{y:.1f}%<extra></extra>",
    )
)

# End marker + a single direct label: lines get their value at the end.
end = window.iloc[-1]
price_fig.add_trace(
    go.Scatter(
        x=[end["ts"]],
        y=[end["price"] * 100],
        mode="markers",
        marker=dict(color=BLUE, size=9, line=dict(color="#0d0d0d", width=2)),
        hoverinfo="skip",
    )
)
price_fig.add_annotation(
    x=end["ts"],
    y=end["price"] * 100,
    text=f"{end['price']:.0%}",
    showarrow=False,
    xanchor="left",
    xshift=12,
    font=dict(family=MONO, size=13, color=INK),
)

apply_chrome(price_fig, height=420)
price_fig.update_layout(hovermode="x unified", margin=dict(l=0, r=64, t=8, b=4))
price_fig.update_xaxes(
    showspikes=True, spikemode="across", spikethickness=1,
    spikecolor=BASELINE, spikedash="solid",
)
price_fig.update_yaxes(
    showgrid=True, gridcolor=GRID, ticksuffix="%", rangemode="tozero",
)

st.plotly_chart(price_fig, use_container_width=True, config={"displayModeBar": False})

# --- Table view — nothing is gated behind a hover --------------------------
st.subheader("Recent points")

table = window.tail(48).iloc[::-1].copy()
table["ts"] = table["ts"].dt.strftime("%Y-%m-%d %H:%M")
table["price"] = table["price"] * 100

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=320,
    column_config={
        "ts": st.column_config.TextColumn("Timestamp (UTC)"),
        "price": st.column_config.NumberColumn("YES", format="%.1f%%"),
    },
)