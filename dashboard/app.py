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

# ── Password gate ────────────────────────────────────────────────────────────────
# Password is stored exclusively in Streamlit Secrets (APP_PASSWORD).
# On Streamlit Cloud: Settings → Secrets → add APP_PASSWORD = "your-password"
# Locally: .streamlit/secrets.toml (never committed to git)
# If APP_PASSWORD secret is not present, the gate is bypassed (local dev only).
def _require_auth() -> None:
    try:
        pw_secret: str = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        pw_secret = ""
    
    if not pw_secret:
        return  # No secret configured — local dev mode, allow through

    if st.session_state.get("_auth_ok"):
        return  # Already authenticated this session

    # ── Render login screen ────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .stApp { background: #F4F6F9; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        _logo_dir_auth = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logo")
        try:
            import base64 as _b64
            with open(os.path.join(_logo_dir_auth, "mcc-logo.png"), "rb") as _f:
                _mcc_auth = _b64.b64encode(_f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;margin-bottom:24px;">'
                f'<img src="data:image/png;base64,{_mcc_auth}" height="80" /></div>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown("### MCC Quality Insights Dashboard", unsafe_allow_html=False)

        st.markdown(
            "<div style='text-align:center;font-size:18px;font-weight:700;"
            "color:#1A1A2E;margin-bottom:4px;'>Quality Insights Dashboard</div>"
            "<div style='text-align:center;font-size:12px;color:#5C6272;"
            "margin-bottom:28px;'>Enterprise Quality Performance — Confidential</div>",
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=True):
            entered = st.text_input("Access Password", type="password",
                                    placeholder="Enter password to continue")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if entered == pw_secret:
                st.session_state["_auth_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

        st.markdown(
            "<div style='text-align:center;font-size:10px;color:#aaa;margin-top:32px;'>"
            "Prepared by Blend for MCC Label Solutions</div>",
            unsafe_allow_html=True,
        )
    st.stop()   # Block all further rendering until authenticated


_require_auth()


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
.stApp { background-color: #F8FAFC; }

/* ── Hide ALL Streamlit chrome — users cannot access source/code ── */
[data-testid="stToolbar"]         { display: none !important; }
[data-testid="stDecoration"]      { display: none !important; }
[data-testid="stStatusWidget"]    { display: none !important; }
header[data-testid="stHeader"]    { background: transparent !important; }
#MainMenu                         { display: none !important; }  /* hamburger ≡ */
footer                            { display: none !important; }  /* "Made with Streamlit" */

/* ── Sidebar ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    box-shadow: 2px 0 8px rgba(0,0,0,0.02);
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
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
    transition: all 0.2s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #4a9dd4;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(109,176,226,0.2);
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
    padding: 20px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    border-radius: 8px;
    box-shadow: 0 1px 6px rgba(109,176,226,.10);
}
.brand-title {
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
    letter-spacing: .5px;
}
.brand-sub {
    font-size: 14px;
    color: #5C6272;
    margin-top: 4px;
    letter-spacing: .2px;
}

/* ── KPI Cards ───────────────────────────────── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px 24px;
    border: 1px solid #E2E8F0;
    border-top: 4px solid #6DB0E2;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
    margin-bottom: 12px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
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
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
    transition: all 0.2s ease;
}
.stDownloadButton > button:hover { 
    background: #259958;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(47,172,103,0.2); 
}

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
    <img src="data:image/png;base64,{_mcc_b64}" height="80" alt="MCC Premium Label Solutions" />
  </div>
  <div style="text-align:center;">
    <div class="brand-title">Quality Insights Dashboard</div>
    <div class="brand-sub">Enterprise Quality Performance — Confidential</div>
  </div>
  <div>
    <img src="data:image/png;base64,{_blend_b64}" height="64" alt="Blend" />
  </div>
</div>
""", unsafe_allow_html=True)


# ── Data loading ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Loading data...")
def load_data() -> pd.DataFrame:
    """
    Load priority:
      1. SQLite (local development / pipeline has run)
      2. Parquet snapshot (Streamlit Cloud — bundled in data/incidents.parquet)
    """
    # 1. SQLite (preferred — always up to date after a pipeline run)
    if os.path.exists(cfg.DB_PATH):
        try:
            conn = sqlite3.connect(cfg.DB_PATH)
            df = pd.read_sql_query(
                "SELECT * FROM quality_incidents", conn,
                parse_dates=["incident_date"],
            )
            conn.close()
            if not df.empty:
                return df
        except Exception:
            pass

    # 2. Parquet snapshot (cloud deployment fallback)
    parquet_path = os.path.join(_root, "data", "incidents.parquet")
    if os.path.exists(parquet_path):
        return pd.read_parquet(parquet_path)

    return pd.DataFrame()


df_all = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sidebar logo
    st.markdown(f"""
    <div style="text-align:center;padding:12px 0 4px 0;">
      <img src="data:image/png;base64,{_mcc_b64}" height="70" alt="MCC" />
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
      <img src="data:image/png;base64,{_blend_b64}" height="45" alt="Blend" />
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
    st.Page("pages/01_overview.py",   title="Overview", icon="📊"),
    st.Page("pages/05_automated_alerts.py", title="Automated Alerts", icon="🚨"),
    st.Page("pages/02_drilldown.py",  title="Incident Detail", icon="🔍"),
    st.Page("pages/03_root_cause.py", title="Root Cause Analysis", icon="🔬"),
    st.Page("pages/04_scorecard.py",  title="Customer Scorecard", icon="📈"),
])
pg.run()
