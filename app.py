"""Streamlit dashboard for Polymarket prediction markets."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from polymarket import load_markets

# --- Design tokens ---------------------------------------------------------
INK = "#0b0b0b"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

BLUE_LIGHT = "#86b6ef"
BLUE_DARK = "#0d366b"
YES_BLUE = "#2a78d6"
NO_RED = "#e34948"

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


st.set_page_config(page_title="Polymarket Dashboard", page_icon="📊", layout="wide")


@st.cache_data(ttl=300)
def get_data():
    """Load markets once and reuse the result for 5 minutes."""
    return pd.DataFrame(load_markets())


def style_axes(fig, x_grid=True):
    """Apply the shared chart chrome: recessive grid, muted ink, no clutter."""
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family=FONT, color=INK, size=13),
        margin=dict(l=8, r=24, t=8, b=8),
        showlegend=False,
        hoverlabel=dict(font_family=FONT, font_size=13),
    )
    fig.update_xaxes(
        showgrid=x_grid,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        linecolor=BASELINE,
        tickfont=dict(color=INK_MUTED, size=12),
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor=BASELINE,
        tickfont=dict(color=INK, size=12),
    )
    return fig


def shorten(text, width=58):
    """Trim long market questions so y-axis labels stay readable."""
    return text if len(text) <= width else text[: width - 1] + "…"


# --- Header ----------------------------------------------------------------
st.title("Polymarket Dashboard")
st.caption("Live prediction-market data from the public Gamma API")

with st.spinner("Loading markets…"):
    df = get_data()

if df.empty:
    st.error("No markets returned by the API.")
    st.stop()

# --- Sidebar filters -------------------------------------------------------
st.sidebar.header("Filters")

search = st.sidebar.text_input("Search question", placeholder="bitcoin, election…")

min_volume = st.sidebar.slider(
    "Minimum volume, $",
    min_value=0,
    max_value=1_000_000,
    value=10_000,
    step=10_000,
    format="$%d",
)

top_n = st.sidebar.slider("Markets shown in charts", 5, 25, 15)

if st.sidebar.button("Refresh data"):
    get_data.clear()
    st.rerun()

view = df[df["volume"] >= min_volume]
if search:
    view = view[view["question"].str.contains(search, case=False, na=False)]

if view.empty:
    st.warning("No markets match these filters. Try lowering the volume threshold.")
    st.stop()

# --- KPI row ---------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Markets", f"{len(view):,}")
col2.metric("Total volume", f"${view['volume'].sum():,.0f}")
col3.metric("Total liquidity", f"${view['liquidity'].sum():,.0f}")
col4.metric("Median probability", f"{view['probability'].median():.0%}")

st.divider()

# --- Chart 1: magnitude — one hue, more is darker --------------------------
st.subheader(f"Top {top_n} markets by volume")

top = view.head(top_n).iloc[::-1]
labels = [shorten(q) for q in top["question"]]

volume_fig = go.Figure(
    go.Bar(
        x=top["volume"],
        y=labels,
        orientation="h",
        marker=dict(
            color=top["volume"],
            colorscale=[[0, BLUE_LIGHT], [1, BLUE_DARK]],
            showscale=False,
            cornerradius=4,
        ),
        customdata=top[["probability"]].to_numpy(),
        hovertemplate="<b>%{y}</b><br>Volume $%{x:,.0f}<br>"
        "YES %{customdata[0]:.0%}<extra></extra>",
    )
)
volume_fig.update_xaxes(tickprefix="$", tickformat="~s")
style_axes(volume_fig)
volume_fig.update_layout(height=32 * len(top) + 60)

st.plotly_chart(volume_fig, use_container_width=True, config={"displayModeBar": False})

# --- Chart 2: polarity — diverging around the 50/50 line -------------------
st.subheader("Which way the market leans")
st.caption("Distance from a 50/50 coin flip. Blue leans YES, red leans NO.")

lean = top["probability"] * 100 - 50

lean_fig = go.Figure(
    go.Bar(
        x=lean,
        y=labels,
        orientation="h",
        marker=dict(
            color=[YES_BLUE if v >= 0 else NO_RED for v in lean],
            cornerradius=4,
        ),
        customdata=top[["probability"]].to_numpy(),
        hovertemplate="<b>%{y}</b><br>YES %{customdata[0]:.0%}<extra></extra>",
    )
)
lean_fig.update_xaxes(
    range=[-52, 52],
    tickvals=[-50, -25, 0, 25, 50],
    ticktext=["0%", "25%", "50%", "75%", "100%"],
)
style_axes(lean_fig)
lean_fig.add_vline(x=0, line_width=1, line_color=BASELINE)
lean_fig.update_layout(height=32 * len(top) + 60)

st.plotly_chart(lean_fig, use_container_width=True, config={"displayModeBar": False})

# --- Table -----------------------------------------------------------------
st.subheader("All markets")

table = view[["question", "probability", "volume", "liquidity", "end_date"]]

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "question": st.column_config.TextColumn("Market", width="large"),
        "probability": st.column_config.ProgressColumn(
            "YES", format="%.0f%%", min_value=0, max_value=1
        ),
        "volume": st.column_config.NumberColumn("Volume", format="$%d"),
        "liquidity": st.column_config.NumberColumn("Liquidity", format="$%d"),
        "end_date": st.column_config.TextColumn("Ends"),
    },
)