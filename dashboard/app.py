"""
app.py — Streamlit multi-page dashboard entry point.
MCC Quality Insights Dashboard — Prepared by Blend for MCC Label Solutions.

Run: streamlit run dashboard/app.py
"""
import os
import sys
import sqlite3
import base64

import pandas as pd
import streamlit as st

# ── Path bootstrap ──────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

import config as cfg

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=cfg.DASHBOARD_TITLE,
    page_icon=os.path.join(_root, "logo", "mcc-logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── MCC Brand Palette ───────────────────────────────────────────────────────────
# Primary Blue: #6DB0E2   Green: #2FAC67   Accent Yellow: #FED742
# Background: #FFFFFF / #F4F6F9   Text: #1A1A2E   Secondary text: #5C6272

MCC_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1A1A2E;
}

/* ── Main background ─────────────────────────── */
.stApp { background-color: #F4F6F9; }

/* ── Sidebar ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 3px solid #6DB0E2;
}
section[data-testid="stSidebar"] * { color: #1A1A2E !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #1A1A2E !important;
    font-weight: 600;
}
section[data-testid="stSidebar"] .stMarkdown hr {
    border-color: #6DB0E2;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #6DB0E2;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #4a9dd4;
}

/* ── Page header bar ─────────────────────────── */
.page-header {
    background: #FFFFFF;
    border-left: 5px solid #6DB0E2;
    border-bottom: 1px solid #E0E6EF;
    color: #1A1A2E;
    padding: 16px 24px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(109,176,226,.12);
}
.page-header h2 {
    margin: 0 0 4px 0;
    font-size: 20px;
    font-weight: 700;
    color: #1A1A2E;
}
.page-header p {
    margin: 0;
    font-size: 13px;
    color: #5C6272;
}

/* ── Top branded header bar ──────────────────── */
.brand-header {
    background: #FFFFFF;
    border-bottom: 3px solid #6DB0E2;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    border-radius: 8px;
    box-shadow: 0 1px 6px rgba(109,176,226,.10);
}
.brand-title {
    font-size: 15px;
    font-weight: 600;
    color: #1A1A2E;
    letter-spacing: .3px;
}
.brand-sub {
    font-size: 11px;
    color: #5C6272;
    margin-top: 2px;
    letter-spacing: .2px;
}

/* ── KPI Cards ───────────────────────────────── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 8px;
    padding: 18px 22px;
    box-shadow: 0 2px 8px rgba(109,176,226,.10);
    border-top: 4px solid #6DB0E2;
    margin-bottom: 8px;
}
.kpi-card.green  { border-top-color: #2FAC67; }
.kpi-card.yellow { border-top-color: #FED742; }
.kpi-card.grey   { border-top-color: #5C6272; }

.kpi-label {
    font-size: 11px;
    color: #5C6272;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #1A1A2E;
    line-height: 1.2;
}
.kpi-value.blue   { color: #6DB0E2; }
.kpi-value.green  { color: #2FAC67; }
.kpi-value.yellow { color: #C9A200; } /* darkened yellow for readability on white */

/* ── Section headings ────────────────────────── */
h1, h2, h3 { color: #1A1A2E; font-weight: 700; }

/* ── Streamlit metric widget override ────────── */
[data-testid="stMetricValue"] { color: #1A1A2E; }

/* ── Dataframe headers ───────────────────────── */
.stDataFrame thead th {
    background-color: #6DB0E2 !important;
    color: #FFFFFF !important;
    font-weight: 600;
}

/* ── Download button ─────────────────────────── */
.stDownloadButton > button {
    background: #2FAC67;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    padding: 8px 20px;
}
.stDownloadButton > button:hover { background: #259958; }

/* ── Tabs ────────────────────────────────────── */
button[data-baseweb="tab"] { font-weight: 600; color: #1A1A2E; }
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #6DB0E2 !important;
    color: #6DB0E2 !important;
}

/* ── Sidebar divider accent ──────────────────── */
.sidebar-accent {
    height: 3px;
    background: linear-gradient(90deg, #6DB0E2, #2FAC67, #FED742);
    border-radius: 2px;
    margin: 8px 0 16px 0;
}

/* ── Multiselect tags (override Streamlit default red) ──── */
[data-baseweb="tag"] {
    background-color: #6DB0E2 !important;
    border: none !important;
}
[data-baseweb="tag"] span { color: #FFFFFF !important; font-weight: 500; }
[data-baseweb="tag"] svg  { fill: #FFFFFF !important; }

/* ── Scrollbar ───────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F4F6F9; }
::-webkit-scrollbar-thumb { background: #6DB0E2; border-radius: 4px; }
</style>
"""
st.markdown(MCC_CSS, unsafe_allow_html=True)


# ── Logo helper ─────────────────────────────────────────────────────────────────
def _img_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


_logo_dir = os.path.join(_root, "logo")
_mcc_b64   = _img_b64(os.path.join(_logo_dir, "mcc-logo.png"))
_blend_b64 = _img_b64(os.path.join(_logo_dir, "blend_logo.png"))

# ── Branded top header ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="brand-header">
  <div>
    <img src="data:image/png;base64,{_mcc_b64}" height="42" alt="MCC Premium Label Solutions" />
  </div>
  <div style="text-align:center;">
    <div class="brand-title">Quality Insights Dashboard</div>
    <div class="brand-sub">Enterprise Quality Performance — Confidential</div>
  </div>
  <div>
    <img src="data:image/png;base64,{_blend_b64}" height="34" alt="Blend" />
  </div>
</div>
""", unsafe_allow_html=True)


# ── Data loading ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Loading data from database...")
def load_data():
    if not os.path.exists(cfg.DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(cfg.DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM quality_incidents", conn, parse_dates=["incident_date"]
    )
    conn.close()
    return df


df_all = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sidebar logo
    st.markdown(f"""
    <div style="text-align:center;padding:12px 0 4px 0;">
      <img src="data:image/png;base64,{_mcc_b64}" height="40" alt="MCC" />
    </div>
    <div class="sidebar-accent"></div>
    """, unsafe_allow_html=True)

    st.markdown("**Quality Pipeline Controls**")

    if df_all.empty:
        st.warning("No data found. Run pipeline_runner.py first.")
        sel_sources, sel_plants, sel_dates = [], [], []
    else:
        all_sources = sorted(df_all["source"].dropna().unique().tolist())
        all_plants  = sorted(df_all["plant"].dropna().unique().tolist())
        date_min    = df_all["incident_date"].min()
        date_max    = df_all["incident_date"].max()

        st.markdown("**Filter by Source System**")
        sel_sources = st.multiselect("", all_sources, default=all_sources,
                                     label_visibility="collapsed")
        st.markdown("**Filter by Plant**")
        sel_plants  = st.multiselect("", all_plants, default=all_plants,
                                     label_visibility="collapsed")
        st.markdown("**Date Range**")
        sel_dates   = st.date_input("", value=(date_min, date_max),
                                    label_visibility="collapsed")

        st.markdown("<div class='sidebar-accent'></div>", unsafe_allow_html=True)

        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()

        if "loaded_at" in df_all.columns:
            st.caption(f"Last pipeline run: {df_all['loaded_at'].max()}")

    # Sidebar footer — uses padding/margin (NOT position:fixed) to stay inside the sidebar
    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="border-top:2px solid #E0E6EF;padding-top:14px;margin-top:8px;
                text-align:center;">
      <div style="font-size:10px;color:#5C6272;letter-spacing:.5px;
                  text-transform:uppercase;margin-bottom:8px;">Prepared by</div>
      <img src="data:image/png;base64,{_blend_b64}" height="26" alt="Blend" />
      <div style="font-size:10px;color:#5C6272;margin-top:6px;">for MCC Label Solutions</div>
    </div>
    """, unsafe_allow_html=True)


# ── Apply filters ───────────────────────────────────────────────────────────────
if not df_all.empty:
    df = df_all.copy()
    if sel_sources:
        df = df[df["source"].isin(sel_sources)]
    if sel_plants:
        df = df[df["plant"].isin(sel_plants)]
    if isinstance(sel_dates, (list, tuple)) and len(sel_dates) == 2:
        start, end = pd.Timestamp(sel_dates[0]), pd.Timestamp(sel_dates[1])
        df = df[(df["incident_date"] >= start) & (df["incident_date"] <= end)]
else:
    df = df_all.copy()

# ── Store in session state so all pages can access ──────────────────────────────
st.session_state["df"]      = df
st.session_state["df_all"]  = df_all
st.session_state["mcc_b64"] = _mcc_b64

# ── Navigation ──────────────────────────────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/01_overview.py",   title="Overview"),
    st.Page("pages/02_drilldown.py",  title="Incident Detail"),
    st.Page("pages/03_root_cause.py", title="Root Cause Analysis"),
    st.Page("pages/04_scorecard.py",  title="Customer Scorecard"),
])
pg.run()
