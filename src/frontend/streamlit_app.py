# src/frontend/streamlit_app.py

import io
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pycountry

BACKEND_URL = "http://localhost:8000"

# Optional TTS
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# ----------------------------------------------------
#                 STREAMLIT PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Global Economic Intelligence Agent",
    layout="wide",
)


# ----------------------------------------------------
#                       CSS
# ----------------------------------------------------
st.markdown(
    """
    <style>

    body, .main {
        background-color: #050712 !important;
        color: #E2E8F0 !important;
        font-family: "Inter", system-ui, sans-serif;
    }

    /* Hero Title */
    .hero {
        font-size: 2.7rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00E5FF, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: -4px;
    }

    /* Subtitle */
    .subtitle {
        font-size: 1.1rem;
        color: #94A3B8;
        margin-top: -6px;
        margin-bottom: 14px;
    }

    /* Chips */
    .chip {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(148,163,184,0.4);
        font-size: 0.75rem;
        color: #7DD3FC;
        margin-right: 0.4rem;
        margin-bottom: 0.45rem;
    }

    /* Glass Cards */
    .glass-card {
        padding: 1rem 1.1rem;
        border-radius: 0.9rem;
        background: linear-gradient(145deg, rgba(15,23,42,0.85), rgba(15,23,42,0.6));
        border: 1px solid rgba(56,189,248,0.25);
        box-shadow: 0 0 16px rgba(56,189,248,0.18);
        margin-bottom: 8px;
    }

    /* Section Headings */
    .section {
        font-size: 1.35rem;
        font-weight: 700;
        color: #7DD3FC;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    /* Sidebar Title */
    .sidebar-title {
        font-weight: 700;
        font-size: 1.1rem;
    }

    /* Glow + Floating Logo Animation */
    .logo {
        filter: drop-shadow(0 0 14px #00E5FF);
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-4px); }
        100% { transform: translateY(0px); }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ----------------------------------------------------
#                    SIDEBAR NAVIGATION
# ----------------------------------------------------
st.sidebar.markdown('<div class="sidebar-title">⚙️ Navigation</div>', unsafe_allow_html=True)
section = st.sidebar.radio(
    "",
    ["🏠 Live Dashboard", "💬 Ask the Agent", "📄 Reports"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Global Economic Intelligence Agent v1.0")


# ----------------------------------------------------
#           HERO SECTION WITH FLOATING LOGO
# ----------------------------------------------------
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:18px; margin-bottom: 6px;">
        <img src="assets/logo.png" width="75" class="logo">
        <div>
            <div class="hero">Global Economic Intelligence Agent</div>
            <div class="subtitle">AI-driven macroeconomic insights • PDF RAG • Real-time indicators & reports</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <span class="chip">📡 Live Indicators</span>
    <span class="chip">📘 PDF RAG (IMF / ECB / OECD)</span>
    <span class="chip">🧠 LLM Reasoning</span>
    <span class="chip">🌐 Global Heatmap</span>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =====================================================
#                 🏠 LIVE DASHBOARD
# =====================================================
if section == "🏠 Live Dashboard":

    st.markdown('<div class="section">🌐 Live Economic Indicator Monitor</div>', unsafe_allow_html=True)

    indicator_options = {
        "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
        "Inflation (CPI %)": "FP.CPI.TOTL.ZG",
        "Unemployment (%)": "SL.UEM.TOTL.ZS",
    }

    colA, colB = st.columns([2, 1])

    with colA:
        selected_indicator_label = st.selectbox(
            "Select indicator:",
            list(indicator_options.keys())
        )

    with colB:
        live_country = st.text_input("Country (ISO-2):", value="US")

    # ------- Country Flag -------
    try:
        flag_url = f"https://flagsapi.com/{live_country.upper()}/flat/64.png"
        st.image(flag_url, width=40)
    except:
        pass

    selected_indicator = indicator_options[selected_indicator_label]

    # ------- Fetch Live API Data -------
    try:
        resp = requests.get(
            f"{BACKEND_URL}/macro/live_chart",
            params={"country": live_country, "indicator": selected_indicator},
            timeout=30
        ).json()

        df = pd.DataFrame(resp["values"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = df["date"].astype(int)
        df = df.dropna().sort_values("date")

        # ------- Main Neon Line Chart -------
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines+markers",
            line=dict(color="#00E5FF", width=3),
            marker=dict(color="#00E5FF", size=6),
            hovertemplate="<b>%{y}</b> (%{x})<extra></extra>",
            name=live_country.upper()
        ))
        fig.update_layout(
            template="plotly_dark",
            height=260,
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # ------- Sparkline -------
        spark = go.Figure()
        spark.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines",
            line=dict(color="#38BDF8", width=2),
            hoverinfo="skip"
        ))
        spark.update_layout(
            template="plotly_dark",
            height=80,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        st.caption("Trend sparkline:")
        st.plotly_chart(spark, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load chart: {e}")

    # ------- Global Heatmap -------
    st.markdown('<div class="section">🗺️ Global Economic Heatmap</div>', unsafe_allow_html=True)

    sample_countries = ["US", "DE", "FR", "GB", "NL", "JP", "CN", "IN", "BR", "ZA", "AU", "CA"]
    rows = []

    for c in sample_countries:
        try:
            r = requests.get(
                f"{BACKEND_URL}/macro/live_chart",
                params={"country": c, "indicator": selected_indicator},
                timeout=10
            ).json()

            vals = r.get("values", [])
            if vals:
                alpha3 = pycountry.countries.get(alpha_2=c).alpha_3
                rows.append({"iso3": alpha3, "country": c, "value": float(vals[0]["value"])})
        except:
            continue

    if rows:
        df_map = pd.DataFrame(rows)
        map_fig = px.choropleth(
            df_map,
            locations="iso3",
            color="value",
            hover_name="country",
            color_continuous_scale="Tealrose",
            template="plotly_dark"
        )
        map_fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(map_fig, use_container_width=True)

    st.markdown("---")


# =====================================================
#                 💬 ASK THE ECONOMIST
# =====================================================
if section == "💬 Ask the Agent":

    st.markdown('<div class="section">💬 Ask the AI Economist</div>', unsafe_allow_html=True)

    query = st.text_input(
        "Your question:",
        placeholder="e.g. 'What does the IMF say about Germany’s inflation outlook?'"
    )

    if st.button("Analyze", type="primary"):
        if not query.strip():
            st.warning("Please enter a question.")
            st.stop()

        with st.spinner("Consulting global databases…"):
            result = requests.get(
                f"{BACKEND_URL}/ask-economic",
                params={"query": query},
                timeout=60
            ).json()

        # ------------ Context Cards ------------
        st.markdown('<div class="section">📌 Context Snapshot</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"<div class='glass-card'><b>Country</b><br>{result['country']}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='glass-card'><b>Indicators</b><br>{', '.join(result['indicators_used'])}</div>", unsafe_allow_html=True)
        with c3:
            rag_count = len([p for p in result["rag_passages"].split("- ") if p.strip()])
            st.markdown(f"<div class='glass-card'><b>RAG Matches</b><br>{rag_count}</div>", unsafe_allow_html=True)

        # ------------ Analysis ------------
        st.markdown('<div class="section">🧠 Final Assessment</div>', unsafe_allow_html=True)
        st.markdown(f"<div class='glass-card'>{result['analysis']}</div>", unsafe_allow_html=True)

        # ------------ TTS ------------
        if TTS_AVAILABLE:
            if st.checkbox("🔊 Play audio summary"):
                tts = gTTS(result["analysis"])
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                st.audio(buf, format="audio/mp3")

        # ------------ Multi-Indicator Comparison ------------
        st.markdown('<div class="section">📈 Multi-Indicator Comparison</div>', unsafe_allow_html=True)

        if result["raw_data"]:
            comp = go.Figure()
            for ind in result["raw_data"]:
                dfi = pd.DataFrame(ind["values"])
                dfi["value"] = pd.to_numeric(dfi["value"], errors="coerce")
                dfi["date"] = dfi["date"].astype(int)
                dfi = dfi.dropna()
                comp.add_trace(go.Scatter(
                    x=dfi["date"],
                    y=dfi["value"],
                    mode="lines+markers",
                    name=ind["indicator"]
                ))
            comp.update_layout(
                template="plotly_dark",
                height=260,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(comp, use_container_width=True)

        # ------------ Individual Trend Charts ------------
        st.markdown('<div class="section">📉 Macro Trends</div>', unsafe_allow_html=True)

        for ind in result["raw_data"]:
            dfi = pd.DataFrame(ind["values"])
            dfi["value"] = pd.to_numeric(dfi["value"], errors="coerce")
            dfi["date"] = dfi["date"].astype(int)
            dfi = dfi.dropna()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dfi["date"],
                y=dfi["value"],
                mode="lines+markers",
                line=dict(width=2),
                name=ind["indicator"]
            ))
            fig.update_layout(
                template="plotly_dark",
                height=220,
                margin=dict(l=10, r=10, t=20, b=10),
                title=ind["indicator"]
            )
            st.plotly_chart(fig, use_container_width=True)


# =====================================================
#                      📄 REPORTS SECTION
# =====================================================
if section == "📄 Reports":

    st.markdown('<div class="section">📄 Generate PDF Economic Report</div>', unsafe_allow_html=True)

    query = st.text_input(
        "Question for the report:",
        placeholder="e.g. 'Provide a full Eurozone inflation briefing.'"
    )

    if st.button("Generate PDF"):
        if not query.strip():
            st.warning("Please enter a question.")
            st.stop()

        with st.spinner("Compiling PDF report…"):
            pdf_response = requests.get(
                f"{BACKEND_URL}/report/generate",
                params={"query": query},
                timeout=90
            )

        if pdf_response.status_code == 200:
            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_response.content,
                file_name="Economic_Report.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Unable to generate report. Check backend logs.")
