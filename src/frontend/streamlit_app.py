# src/frontend/streamlit_app.py

import html
import io
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = PROJECT_ROOT / "assets" / "logo.png"

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Economic Intelligence Agent",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# DESIGN SYSTEM
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --bg: #07111f;
        --bg-soft: #0a1626;
        --panel: rgba(12, 27, 47, 0.78);
        --panel-strong: #0d1d31;
        --border: rgba(93, 137, 181, 0.22);
        --border-strong: rgba(61, 217, 255, 0.30);
        --text: #e8f0f8;
        --muted: #8fa7bd;
        --cyan: #3dd9ff;
        --blue: #4d8dff;
        --violet: #8a6cff;
        --green: #35d39a;
        --amber: #f6c768;
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 8%, rgba(61, 217, 255, 0.08), transparent 28%),
            radial-gradient(circle at 88% 16%, rgba(138, 108, 255, 0.09), transparent 30%),
            linear-gradient(180deg, #07111f 0%, #081421 45%, #07111f 100%);
        color: var(--text);
    }

    .block-container {
        max-width: 1480px;
        padding-top: 2.1rem;
        padding-bottom: 4rem;
    }

    #MainMenu, footer, header { visibility: hidden; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1727 0%, #081321 100%);
        border-right: 1px solid rgba(91, 132, 171, 0.17);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.4rem;
    }

    .sidebar-brand {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: var(--cyan);
        margin-bottom: 0.45rem;
    }

    .sidebar-title {
        font-size: 1.15rem;
        font-weight: 750;
        color: var(--text);
        line-height: 1.25;
        margin-bottom: 1rem;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.42rem 0.68rem;
        border-radius: 999px;
        border: 1px solid rgba(53, 211, 154, 0.23);
        background: rgba(53, 211, 154, 0.08);
        color: #7be7bd;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 1.15rem;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 12px rgba(53, 211, 154, 0.85);
    }

    div[role="radiogroup"] label {
        background: transparent;
        border-radius: 10px;
        padding: 0.38rem 0.45rem;
        margin: 0.08rem 0;
        transition: background 160ms ease;
    }

    div[role="radiogroup"] label:hover {
        background: rgba(61, 217, 255, 0.06);
    }

    .hero-shell {
        padding: 1.8rem 2rem;
        border-radius: 22px;
        background:
            linear-gradient(135deg, rgba(13, 31, 52, 0.95), rgba(9, 22, 38, 0.88));
        border: 1px solid var(--border);
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.23);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    .hero-shell::after {
        content: "";
        position: absolute;
        width: 360px;
        height: 360px;
        right: -190px;
        top: -210px;
        background: radial-gradient(circle, rgba(61, 217, 255, 0.18), transparent 65%);
        pointer-events: none;
    }

    .eyebrow {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: var(--cyan);
        margin-bottom: 0.42rem;
    }

    .hero-title {
        font-size: clamp(2rem, 4.2vw, 3.45rem);
        line-height: 1.02;
        font-weight: 850;
        letter-spacing: -0.035em;
        color: #f2f7fb;
        margin: 0;
    }

    .hero-accent {
        background: linear-gradient(90deg, #3dd9ff, #4d8dff 52%, #8a6cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        max-width: 820px;
        margin-top: 0.72rem;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.55;
    }

    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1.15rem;
    }

    .tech-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.38rem;
        padding: 0.42rem 0.68rem;
        border-radius: 999px;
        border: 1px solid rgba(93, 137, 181, 0.24);
        background: rgba(8, 22, 38, 0.65);
        color: #b7caDB;
        font-size: 0.76rem;
        font-weight: 650;
    }

    .section-kicker {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 800;
        color: var(--cyan);
        margin-bottom: 0.28rem;
    }

    .section-title {
        font-size: 1.48rem;
        font-weight: 780;
        color: #ecf5fb;
        letter-spacing: -0.015em;
        margin-bottom: 0.18rem;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.91rem;
        margin-bottom: 1.15rem;
    }

    .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.13);
    }

    .metric-card {
        min-height: 108px;
        border-radius: 15px;
        padding: 1rem 1.05rem;
        background: linear-gradient(145deg, rgba(13, 31, 52, 0.92), rgba(9, 24, 41, 0.84));
        border: 1px solid var(--border);
    }

    .metric-label {
        font-size: 0.70rem;
        font-weight: 760;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: #7792aa;
        margin-bottom: 0.42rem;
    }

    .metric-value {
        font-size: 1.55rem;
        font-weight: 820;
        color: #eef7fd;
        line-height: 1.1;
    }

    .metric-foot {
        color: #7891a8;
        font-size: 0.72rem;
        margin-top: 0.45rem;
    }

    .analysis-card {
        padding: 1.25rem 1.35rem;
        border-radius: 17px;
        background: linear-gradient(145deg, rgba(13, 31, 52, 0.94), rgba(10, 24, 42, 0.88));
        border: 1px solid rgba(61, 217, 255, 0.19);
        color: #dce8f1;
        font-size: 0.97rem;
        line-height: 1.75;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.14);
    }

    .context-card {
        min-height: 98px;
        border-radius: 14px;
        padding: 0.95rem 1rem;
        background: rgba(10, 25, 43, 0.78);
        border: 1px solid var(--border);
    }

    .context-label {
        color: #728da5;
        text-transform: uppercase;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        margin-bottom: 0.38rem;
    }

    .context-value {
        color: #edf6fc;
        font-size: 1rem;
        font-weight: 740;
        word-break: break-word;
    }

    .divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(61,217,255,0.32), rgba(77,141,255,0.08), transparent);
        margin: 1.35rem 0 1.6rem;
    }

    .stTextInput input,
    [data-baseweb="select"] > div {
        background: #0b192b !important;
        border: 1px solid rgba(96, 137, 179, 0.23) !important;
        color: #ecf5fb !important;
        border-radius: 11px !important;
        min-height: 46px;
    }

    .stTextInput input:focus {
        border-color: rgba(61, 217, 255, 0.55) !important;
        box-shadow: 0 0 0 1px rgba(61, 217, 255, 0.18) !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid rgba(61, 217, 255, 0.30);
        background: linear-gradient(135deg, #11304c, #15345a);
        color: #effaff;
        font-weight: 750;
        min-height: 44px;
        transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(61, 217, 255, 0.62);
        transform: translateY(-1px);
        box-shadow: 0 8px 22px rgba(61, 217, 255, 0.08);
        color: #ffffff;
    }

    [data-testid="stExpander"] {
        background: rgba(10, 24, 41, 0.65);
        border: 1px solid var(--border);
        border-radius: 12px;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    .small-note {
        color: #6f879c;
        font-size: 0.76rem;
        line-height: 1.5;
    }

    @media (max-width: 850px) {
        .block-container { padding-top: 1.2rem; }
        .hero-shell { padding: 1.3rem; }
        .hero-title { font-size: 2.1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def section_header(kicker: str, title: str, copy: str = ""):
    st.markdown(
        f"""
        <div class="section-kicker">{html.escape(kicker)}</div>
        <div class="section-title">{html.escape(title)}</div>
        <div class="section-copy">{html.escape(copy)}</div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, foot: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-foot">{html.escape(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def context_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="context-card">
            <div class="context-label">{html.escape(label)}</div>
            <div class="context-value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_json(path: str, params: dict | None = None, timeout: int = 30):
    response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=timeout)
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text or f"HTTP {response.status_code}"
        raise RuntimeError(detail)
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("Backend returned an invalid response.") from exc


def style_figure(fig: go.Figure, height: int = 320, title: str | None = None):
    fig.update_layout(
        template=None,
        height=height,
        margin=dict(l=18, r=18, t=42 if title else 20, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a9bfd2", family="Inter, Arial, sans-serif"),
        title=dict(text=title, font=dict(size=16, color="#e7f2fa")) if title else None,
        xaxis=dict(
            gridcolor="rgba(107,137,166,0.10)",
            zeroline=False,
            linecolor="rgba(107,137,166,0.12)",
        ),
        yaxis=dict(
            gridcolor="rgba(107,137,166,0.10)",
            zeroline=False,
            linecolor="rgba(107,137,166,0.12)",
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=56)

st.sidebar.markdown(
    """
    <div class="sidebar-brand">ECONOMIC INTELLIGENCE</div>
    <div class="sidebar-title">Global Economic<br>Intelligence Agent</div>
    <div class="status-pill"><span class="status-dot"></span> SYSTEM ONLINE</div>
    """,
    unsafe_allow_html=True,
)

section = st.sidebar.radio(
    "Navigation",
    ["Overview", "Ask the Agent", "Reports"],
    label_visibility="collapsed",
)

st.sidebar.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.sidebar.markdown(
    """
    <div class="small-note">
        Live macro data · PDF retrieval · LLM synthesis<br><br>
        v1.0 · FastAPI + Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# HERO
# -----------------------------------------------------------------------------
hero_logo_col, hero_text_col = st.columns([1, 9], gap="medium")

with hero_logo_col:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=82)

with hero_text_col:
    st.markdown(
        """
        <div class="hero-shell">
            <div class="eyebrow">MACRO INTELLIGENCE / LIVE DATA / RAG</div>
            <div class="hero-title">Global Economic <span class="hero-accent">Intelligence Agent</span></div>
            <div class="hero-subtitle">
                A research interface that combines live economic indicators, retrieved document evidence,
                and LLM synthesis into one operational workflow.
            </div>
            <div class="badge-row">
                <span class="tech-badge">LIVE · World Bank</span>
                <span class="tech-badge">RAG · ChromaDB</span>
                <span class="tech-badge">API · FastAPI</span>
                <span class="tech-badge">LLM · OpenAI</span>
                <span class="tech-badge">UI · Streamlit</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# OVERVIEW
# =============================================================================
if section == "Overview":
    section_header(
        "Live intelligence",
        "Macroeconomic monitor",
        "Inspect current indicator trends and compare selected economies from the same interface.",
    )

    indicator_options = {
        "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
        "Inflation (CPI %)": "FP.CPI.TOTL.ZG",
        "Unemployment (%)": "SL.UEM.TOTL.ZS",
    }

    control_left, control_right = st.columns([2, 1], gap="medium")
    with control_left:
        selected_indicator_label = st.selectbox(
            "Indicator",
            list(indicator_options.keys()),
        )
    with control_right:
        live_country = st.text_input("Country (ISO-2)", value="US").strip().upper()

    selected_indicator = indicator_options[selected_indicator_label]

    try:
        resp = get_json(
            "/macro/live_chart",
            params={"country": live_country, "indicator": selected_indicator},
            timeout=30,
        )

        df = pd.DataFrame(resp.get("values", []))
        if df.empty:
            raise RuntimeError("No indicator data returned for this country.")

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = pd.to_numeric(df["date"], errors="coerce")
        df = df.dropna().sort_values("date")

        if df.empty:
            raise RuntimeError("No usable indicator data returned for this country.")

        latest = df.iloc[-1]
        prior = df.iloc[-2] if len(df) > 1 else latest
        delta = latest["value"] - prior["value"]
        delta_text = f"{delta:+.2f} vs prior point"

        m1, m2, m3, m4 = st.columns(4, gap="medium")
        with m1:
            metric_card("Country", live_country, "ISO-2 market")
        with m2:
            metric_card("Latest value", f"{latest['value']:.2f}", selected_indicator_label)
        with m3:
            metric_card("Latest period", str(int(latest["date"])), "Most recent observation")
        with m4:
            metric_card("Point change", f"{delta:+.2f}", delta_text)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        chart_left, chart_right = st.columns([2.25, 1], gap="large")

        with chart_left:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["value"],
                    mode="lines+markers",
                    line=dict(color="#3dd9ff", width=3),
                    marker=dict(color="#8a6cff", size=6, line=dict(width=1, color="#d8f7ff")),
                    fill="tozeroy",
                    fillcolor="rgba(61,217,255,0.035)",
                    hovertemplate="<b>%{y:.2f}</b><br>%{x}<extra></extra>",
                    name=live_country,
                )
            )
            style_figure(fig, height=390, title=f"{selected_indicator_label} · {live_country}")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with chart_right:
            section_header("Signal", "Recent direction", "Most recent observations")
            recent = df.tail(5).sort_values("date", ascending=False)
            for _, row in recent.iterrows():
                st.markdown(
                    f"""
                    <div class="context-card" style="min-height:70px; margin-bottom:0.55rem;">
                        <div class="context-label">{int(row['date'])}</div>
                        <div class="context-value">{row['value']:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        st.error(f"Could not load live indicator data: {exc}")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    section_header(
        "Cross-market view",
        "Global comparison",
        "A fast visual scan across selected major economies for the active indicator.",
    )

    sample_countries = ["US", "DE", "FR", "GB", "NL", "JP", "CN", "IN", "BR", "ZA", "AU", "CA"]
    rows = []

    for country_code in sample_countries:
        try:
            data = get_json(
                "/macro/live_chart",
                params={"country": country_code, "indicator": selected_indicator},
                timeout=10,
            )
            vals = data.get("values", [])
            if vals:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                if country_obj:
                    rows.append(
                        {
                            "iso3": country_obj.alpha_3,
                            "country": country_obj.name,
                            "value": float(vals[0]["value"]),
                        }
                    )
        except Exception:
            continue

    if rows:
        df_map = pd.DataFrame(rows)
        map_fig = px.choropleth(
            df_map,
            locations="iso3",
            color="value",
            hover_name="country",
            color_continuous_scale=[
                [0.0, "#182b47"],
                [0.35, "#245d86"],
                [0.7, "#3dd9ff"],
                [1.0, "#8a6cff"],
            ],
        )
        map_fig.update_geos(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
            landcolor="#0c1a2c",
        )
        map_fig.update_layout(
            height=440,
            margin=dict(l=0, r=0, t=12, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a9bfd2"),
            coloraxis_colorbar=dict(title="Value", thickness=10, len=0.55),
        )
        st.plotly_chart(map_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No comparison data is currently available.")


# =============================================================================
# ASK THE AGENT
# =============================================================================
elif section == "Ask the Agent":
    section_header(
        "Grounded reasoning",
        "Ask the AI Economist",
        "The agent combines live macro data with retrieved report passages before synthesizing an answer.",
    )

    query = st.text_input(
        "Research question",
        placeholder="e.g. What is the recent inflation outlook for Germany?",
    )

    action_col, note_col = st.columns([1, 5], gap="medium")
    with action_col:
        analyze = st.button("Run analysis", type="primary", use_container_width=True)
    with note_col:
        st.markdown(
            "<div class='small-note' style='padding-top:0.65rem;'>Uses live indicators + vector retrieval + LLM synthesis.</div>",
            unsafe_allow_html=True,
        )

    if analyze:
        if not query.strip():
            st.warning("Enter a research question first.")
            st.stop()

        try:
            with st.spinner("Retrieving economic evidence and synthesizing analysis…"):
                result = get_json(
                    "/ask-economic",
                    params={"query": query},
                    timeout=90,
                )

            rag_passages = result.get("rag_passages", "") or ""
            rag_count = len([p for p in rag_passages.split("- ") if p.strip()])

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            section_header("Evidence context", "Analysis context")

            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                context_card("Detected country", result.get("country", "—"))
            with c2:
                indicators = ", ".join(result.get("indicators_used", [])) or "—"
                context_card("Indicators", indicators)
            with c3:
                context_card("Retrieved passages", str(rag_count))

            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            section_header("Synthesis", "Final assessment")
            safe_analysis = html.escape(result.get("analysis", "No analysis returned.")).replace("\n", "<br>")
            st.markdown(
                f"<div class='analysis-card'>{safe_analysis}</div>",
                unsafe_allow_html=True,
            )

            if TTS_AVAILABLE:
                with st.expander("Audio summary"):
                    if st.button("Generate audio", key="tts_generate"):
                        tts = gTTS(result.get("analysis", ""))
                        buf = io.BytesIO()
                        tts.write_to_fp(buf)
                        buf.seek(0)
                        st.audio(buf, format="audio/mp3")

            if rag_passages:
                with st.expander("Retrieved document context"):
                    st.text(rag_passages)

            raw_data = result.get("raw_data", [])
            if raw_data:
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                section_header("Data layer", "Macro trend comparison")

                comp = go.Figure()
                palette = ["#3dd9ff", "#8a6cff", "#35d39a", "#f6c768"]
                for idx, indicator_data in enumerate(raw_data):
                    dfi = pd.DataFrame(indicator_data.get("values", []))
                    if dfi.empty:
                        continue
                    dfi["value"] = pd.to_numeric(dfi["value"], errors="coerce")
                    dfi["date"] = pd.to_numeric(dfi["date"], errors="coerce")
                    dfi = dfi.dropna().sort_values("date")
                    comp.add_trace(
                        go.Scatter(
                            x=dfi["date"],
                            y=dfi["value"],
                            mode="lines+markers",
                            name=indicator_data.get("indicator", f"Indicator {idx + 1}"),
                            line=dict(width=2.5, color=palette[idx % len(palette)]),
                            marker=dict(size=5),
                        )
                    )

                style_figure(comp, height=350)
                st.plotly_chart(comp, use_container_width=True, config={"displayModeBar": False})

        except Exception as exc:
            st.error(f"Analysis could not be completed: {exc}")


# =============================================================================
# REPORTS
# =============================================================================
elif section == "Reports":
    section_header(
        "Stakeholder output",
        "Generate an economic briefing",
        "Create a downloadable PDF briefing from the same live-data and RAG-backed analysis pipeline.",
    )

    st.markdown(
        """
        <div class="panel" style="margin-bottom:1rem;">
            <div class="context-label">REPORT WORKFLOW</div>
            <div style="color:#dce9f2; font-size:0.95rem; line-height:1.65;">
                01 · Interpret the research question &nbsp;&nbsp;→&nbsp;&nbsp;
                02 · Retrieve macro + document context &nbsp;&nbsp;→&nbsp;&nbsp;
                03 · Synthesize analysis &nbsp;&nbsp;→&nbsp;&nbsp;
                04 · Render PDF briefing
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    report_query = st.text_input(
        "Briefing request",
        placeholder="e.g. Provide an economic briefing on Germany's inflation outlook.",
    )

    if st.button("Generate PDF briefing", type="primary"):
        if not report_query.strip():
            st.warning("Enter a briefing request first.")
            st.stop()

        try:
            with st.spinner("Building economic briefing…"):
                pdf_response = requests.get(
                    f"{BACKEND_URL}/report/generate",
                    params={"query": report_query},
                    timeout=120,
                )

            if not pdf_response.ok:
                try:
                    detail = pdf_response.json().get("detail", pdf_response.text)
                except ValueError:
                    detail = pdf_response.text or f"HTTP {pdf_response.status_code}"
                raise RuntimeError(detail)

            st.success("Briefing generated successfully.")
            st.download_button(
                "Download PDF briefing",
                data=pdf_response.content,
                file_name="Economic_Report.pdf",
                mime="application/pdf",
            )

        except Exception as exc:
            st.error(f"Unable to generate report: {exc}")
