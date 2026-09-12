"""Shared design tokens and chart chrome for the Polymarket terminal."""

import streamlit as st

# --- Tokens ----------------------------------------------------------------
PAGE = "#0d0d0d"
PANEL = "#131312"
GRID = "#2c2c2a"
BASELINE = "#383835"

INK = "#ffffff"
INK_DIM = "#c3c2b7"
INK_MUTED = "#898781"

BLUE = "#3987e5"
BLUE_WASH = "rgba(57, 135, 229, 0.12)"
RED = "#e66767"
RAMP = [[0.0, "#86b6ef"], [0.5, "#3987e5"], [1.0, "#184f95"]]

MONO = 'ui-monospace, "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace'


# --- Helpers ---------------------------------------------------------------
def compact_money(value):
    """Render 3_080_195_416 as $3.1B — stat tiles get compact figures."""
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= threshold:
            return f"${value / threshold:.1f}{suffix}"
    return f"${value:,.0f}"


def shorten(text, width=52):
    """Trim long questions so axis labels never collide."""
    return text if len(text) <= width else text[: width - 1] + "…"


def inject_css():
    """Terminal styling — call once at the top of every page."""
    st.markdown(
        f"""
        <style>
          html, body, [class*="css"], .stApp {{ font-family: {MONO}; }}
          .stApp {{ background: {PAGE}; }}
          #MainMenu, footer {{ visibility: hidden; }}
          .block-container {{ padding-top: 2.5rem; max-width: 1400px; }}

          section[data-testid="stSidebar"] {{
            background: {PANEL}; border-right: 1px solid {GRID};
          }}

          .term-bar {{
            display: flex; justify-content: space-between; align-items: baseline;
            border-bottom: 1px solid {GRID}; padding-bottom: .75rem;
            margin-bottom: 1.5rem;
          }}
          .term-title {{
            font-size: 1.05rem; letter-spacing: .18em; text-transform: uppercase;
            color: {INK}; font-weight: 600;
          }}
          .term-meta {{
            font-size: .75rem; color: {INK_MUTED}; letter-spacing: .08em;
          }}

          [data-testid="stMetric"] {{
            background: {PANEL}; border: 1px solid {GRID};
            padding: .9rem 1.1rem; border-radius: 4px;
          }}
          [data-testid="stMetricLabel"] p {{
            font-size: .68rem !important; letter-spacing: .14em;
            text-transform: uppercase; color: {INK_MUTED} !important;
          }}
          [data-testid="stMetricValue"] {{
            font-size: 1.6rem !important; color: {INK} !important; font-weight: 600;
          }}

          h3 {{
            font-size: .8rem !important; letter-spacing: .16em;
            text-transform: uppercase; color: {INK_DIM} !important;
            margin-top: 2.2rem !important;
          }}
          .term-note {{
            font-size: .72rem; color: {INK_MUTED}; margin: -.4rem 0 .8rem;
          }}

          .hero-label {{
            font-size: .68rem; letter-spacing: .14em; text-transform: uppercase;
            color: {INK_MUTED};
          }}
          .hero-value {{
            font-size: 3.4rem; font-weight: 600; color: {INK};
            line-height: 1.05; margin-top: .1rem;
          }}
          .hero-question {{
            font-size: .95rem; color: {INK_DIM}; margin-top: .5rem;
            max-width: 60ch;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def term_header(meta):
    """The thin uppercase bar every page opens with."""
    st.markdown(
        f"""
        <div class="term-bar">
          <div class="term-title">◧ Polymarket Terminal</div>
          <div class="term-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chrome(fig, height):
    """Shared 2D chart chrome: hairline grid, muted ink, no decoration."""
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