"""Overview page — the market landscape at a glance."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import get_markets
from theme import (
    BASELINE, BLUE, GRID, INK_MUTED, MONO, PAGE, PANEL, RAMP, RED,
    apply_chrome, compact_money, inject_css, shorten, term_header,
)

st.set_page_config(page_title="Polymarket Terminal", page_icon="◧", layout="wide")
inject_css()

df = get_markets()
term_header(
    f"GAMMA API · {len(df)} MARKETS · {pd.Timestamp.now():%Y-%m-%d %H:%M}"
)

if df.empty:
    st.error("No markets returned by the API.")
    st.stop()

# --- Filter row (one row, scopes everything below) -------------------------
f1, f2, f3, f4 = st.columns([2, 2, 2, 1])

search = f1.text_input("Search", placeholder="bitcoin, election, fed…")
min_volume = f2.select_slider(
    "Min volume",
    options=[0, 10_000, 100_000, 500_000, 1_000_000, 5_000_000],
    value=100_000,
    format_func=compact_money,
)
prob_range = f3.slider("Probability range, %", 0, 100, (2, 98))
top_n = f4.number_input("Rows", min_value=5, max_value=30, value=14, step=1)

low, high = prob_range
view = df[
    (df["volume"] >= min_volume)
    & (df["probability"] * 100 >= low)
    & (df["probability"] * 100 <= high)
]
if search:
    view = view[view["question"].str.contains(search, case=False, na=False)]

if view.empty:
    st.warning("No markets match these filters. Widen the probability range.")
    st.stop()

# --- KPI row ---------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Markets", f"{len(view):,}")
k2.metric("Volume", compact_money(view["volume"].sum()))
k3.metric("Liquidity", compact_money(view["liquidity"].sum()))
k4.metric("Median odds", f"{view['probability'].median():.0%}")

# --- Jump to the detail page -----------------------------------------------
st.subheader("Inspect a market")

pick = st.selectbox(
    "Market",
    options=view.index,
    format_func=lambda i: shorten(view.loc[i, "question"], 90),
    label_visibility="collapsed",
)
if st.button("Open price history →"):
    st.session_state["selected_question"] = view.loc[pick, "question"]
    st.switch_page("pages/1_Market_detail.py")

# --- Chart 1: magnitude — one series, one color ----------------------------
st.subheader("Volume leaders")

top = view.head(int(top_n)).iloc[::-1]
labels = [shorten(q) for q in top["question"]]

volume_fig = go.Figure(
    go.Bar(
        x=top["volume"],
        y=labels,
        orientation="h",
        width=0.62,
        marker=dict(color=BLUE, cornerradius=4),
        customdata=top[["probability"]].to_numpy(),
        hovertemplate="%{y}<br>volume %{x:$,.0f} · yes %{customdata[0]:.0%}"
        "<extra></extra>",
    )
)
volume_fig.update_xaxes(tickprefix="$", tickformat="~s")
apply_chrome(volume_fig, height=30 * len(top) + 50)
st.plotly_chart(volume_fig, use_container_width=True, config={"displayModeBar": False})

# --- Chart 2: polarity — diverging around the coin flip --------------------
st.subheader("Conviction")
st.markdown(
    '<div class="term-note">Distance from a 50/50 coin flip. '
    "Blue leans YES, red leans NO.</div>",
    unsafe_allow_html=True,
)

lean = top["probability"] * 100 - 50

lean_fig = go.Figure(
    go.Bar(
        x=lean,
        y=labels,
        orientation="h",
        width=0.62,
        marker=dict(color=[BLUE if v >= 0 else RED for v in lean], cornerradius=4),
        customdata=top[["probability"]].to_numpy(),
        hovertemplate="%{y}<br>yes %{customdata[0]:.0%}<extra></extra>",
    )
)
lean_fig.update_xaxes(
    range=[-52, 52],
    tickvals=[-50, -25, 0, 25, 50],
    ticktext=["0%", "25%", "50%", "75%", "100%"],
)
apply_chrome(lean_fig, height=30 * len(top) + 50)
lean_fig.add_vline(x=0, line_width=1, line_color=BASELINE)
st.plotly_chart(lean_fig, use_container_width=True, config={"displayModeBar": False})

# --- Chart 3: the 3D explorer ----------------------------------------------
st.subheader("Market landscape")
st.markdown(
    '<div class="term-note">Drag to rotate · scroll to zoom. '
    "Four dimensions at once — exact values live in the table below.</div>",
    unsafe_allow_html=True,
)

cloud = view[(view["volume"] > 0) & (view["liquidity"] > 0)].copy()
cloud = cloud.dropna(subset=["days_left"])
cloud = cloud[cloud["days_left"].between(0, 730)]

if len(cloud) < 3:
    st.info("Not enough markets with a valid end date to plot the landscape.")
else:
    axis_style = dict(
        backgroundcolor=PAGE, gridcolor=GRID, zerolinecolor=BASELINE,
        showbackground=True, color=INK_MUTED,
        title_font=dict(size=11, color=INK_MUTED),
        tickfont=dict(size=10, color=INK_MUTED),
    )

    space_fig = go.Figure(
        go.Scatter3d(
            x=cloud["volume"],
            y=cloud["liquidity"],
            z=cloud["days_left"],
            mode="markers",
            marker=dict(
                size=5,
                color=cloud["probability"] * 100,
                colorscale=RAMP,
                cmin=0,
                cmax=100,
                opacity=0.9,
                line=dict(width=0),
                colorbar=dict(
                    title=dict(text="YES %", font=dict(size=10, color=INK_MUTED)),
                    thickness=10, len=0.6, outlinewidth=0,
                    tickfont=dict(size=10, color=INK_MUTED),
                ),
            ),
            text=[shorten(q, 60) for q in cloud["question"]],
            customdata=cloud[["probability"]].to_numpy(),
            hovertemplate="%{text}<br>volume %{x:$,.0f} · liquidity %{y:$,.0f}"
            "<br>%{z:.0f} days left · yes %{customdata[0]:.0%}<extra></extra>",
        )
    )
    space_fig.update_layout(
        height=620,
        paper_bgcolor=PAGE,
        font=dict(family=MONO, color=INK_MUTED, size=11),
        margin=dict(l=0, r=0, t=0, b=0),
        hoverlabel=dict(
            font_family=MONO, font_size=12, bgcolor=PANEL, bordercolor=GRID
        ),
        scene=dict(
            xaxis=dict(title="volume $", type="log", **axis_style),
            yaxis=dict(title="liquidity $", type="log", **axis_style),
            zaxis=dict(title="days to close", **axis_style),
            camera=dict(eye=dict(x=1.6, y=1.5, z=0.9)),
        ),
    )
    st.plotly_chart(
        space_fig, use_container_width=True, config={"displayModeBar": False}
    )

# --- Table view ------------------------------------------------------------
st.subheader("All markets")

st.dataframe(
    view[["question", "probability", "volume", "liquidity", "days_left", "end_date"]],
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        "question": st.column_config.TextColumn("Market", width="large"),
        "probability": st.column_config.ProgressColumn(
            "YES", format="%.0f%%", min_value=0, max_value=1
        ),
        "volume": st.column_config.NumberColumn("Volume", format="$%d"),
        "liquidity": st.column_config.NumberColumn("Liquidity", format="$%d"),
        "days_left": st.column_config.NumberColumn("Days left", format="%d"),
        "end_date": st.column_config.TextColumn("Ends"),
    },
)