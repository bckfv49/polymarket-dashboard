"""Polymarket terminal — a dark, minimal dashboard over the public Gamma API."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from polymarket import load_markets

# --- Design tokens ---------------------------------------------------------
PAGE = "#0d0d0d"
PANEL = "#131312"
GRID = "#2c2c2a"
BASELINE = "#383835"

INK = "#ffffff"
INK_DIM = "#c3c2b7"
INK_MUTED = "#898781"

BLUE = "#3987e5"
RED = "#e66767"
RAMP = [[0.0, "#86b6ef"], [0.5, "#3987e5"], [1.0, "#184f95"]]

MONO = 'ui-monospace, "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace'

st.set_page_config(page_title="Polymarket Terminal", page_icon="◧", layout="wide")

st.markdown(
    f"""
    <style>
      html, body, [class*="css"], .stApp {{ font-family: {MONO}; }}
      .stApp {{ background: {PAGE}; }}
      #MainMenu, footer, header {{ visibility: hidden; }}
      .block-container {{ padding-top: 2.5rem; max-width: 1400px; }}

      .term-bar {{
        display: flex; justify-content: space-between; align-items: baseline;
        border-bottom: 1px solid {GRID}; padding-bottom: .75rem; margin-bottom: 1.5rem;
      }}
      .term-title {{
        font-size: 1.05rem; letter-spacing: .18em; text-transform: uppercase;
        color: {INK}; font-weight: 600;
      }}
      .term-meta {{ font-size: .75rem; color: {INK_MUTED}; letter-spacing: .08em; }}

      [data-testid="stMetric"] {{
        background: {PANEL}; border: 1px solid {GRID};
        padding: .9rem 1.1rem; border-radius: 4px;
      }}
      [data-testid="stMetricLabel"] p {{
        font-size: .68rem !important; letter-spacing: .14em; text-transform: uppercase;
        color: {INK_MUTED} !important;
      }}
      [data-testid="stMetricValue"] {{
        font-size: 1.6rem !important; color: {INK} !important; font-weight: 600;
      }}

      h3 {{
        font-size: .8rem !important; letter-spacing: .16em; text-transform: uppercase;
        color: {INK_DIM} !important; margin-top: 2.2rem !important;
      }}
      .term-note {{ font-size: .72rem; color: {INK_MUTED}; margin: -.4rem 0 .8rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def get_data():
    """Load markets once and reuse the result for five minutes."""
    df = pd.DataFrame(load_markets())
    end = pd.to_datetime(df["end_date"], errors="coerce", utc=True)
    df["days_left"] = (end - pd.Timestamp.now(tz="UTC")).dt.days
    return df


def compact_money(value):
    """Render 3_080_195_416 as $3.1B — stat tiles get compact figures."""
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= threshold:
            return f"${value / threshold:.1f}{suffix}"
    return f"${value:,.0f}"


def shorten(text, width=52):
    """Trim long questions so axis labels never collide."""
    return text if len(text) <= width else text[: width - 1] + "…"


def apply_chrome(fig, height):
    """Shared chart chrome: hairline grid, muted ink, no decoration."""
    fig.update_layout(
        height=height,
        paper_bgcolor=PAGE,
        plot_bgcolor=PAGE,
        font=dict(family=MONO, color=INK_DIM, size=12),
        margin=dict(l=0, r=16, t=4, b=4),
        showlegend=False,
        bargap=0.38,
        hoverlabel=dict(
            font_family=MONO, font_size=12, bgcolor=PANEL, bordercolor=GRID
        ),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
        linecolor=BASELINE, tickfont=dict(color=INK_MUTED, size=11),
    )
    fig.update_yaxes(
        showgrid=False, zeroline=False, linecolor=BASELINE,
        tickfont=dict(color=INK_DIM, size=11),
    )
    return fig


# --- Header ----------------------------------------------------------------
df = get_data()

st.markdown(
    f"""
    <div class="term-bar">
      <div class="term-title">◧ Polymarket Terminal</div>
      <div class="term-meta">
        GAMMA API · {len(df)} MARKETS · {pd.Timestamp.now():%Y-%m-%d %H:%M}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
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
        backgroundcolor=PAGE,
        gridcolor=GRID,
        zerolinecolor=BASELINE,
        showbackground=True,
        color=INK_MUTED,
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
                    thickness=10,
                    len=0.6,
                    outlinewidth=0,
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
        font=dict(family=MONO, color=INK_DIM, size=11),
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

# --- Table view (every value reachable without hovering) -------------------
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