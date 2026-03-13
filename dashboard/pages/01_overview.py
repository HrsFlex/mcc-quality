"""
01_overview.py — Enterprise Quality Overview — MCC Label Solutions
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# MCC Brand Colors
MCC_BLUE   = "#6DB0E2"
MCC_GREEN  = "#2FAC67"
MCC_YELLOW = "#FED742"
MCC_DARK   = "#1A1A2E"
MCC_GREY   = "#5C6272"
MCC_BG     = "#F4F6F9"

PALETTE = [MCC_BLUE, MCC_GREEN, "#C9A200", "#4a9dd4", "#259958", "#8ecae6"]

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h2>Enterprise Quality Overview</h2>
  <p>Consolidated quality performance metrics across all plants, customers, and ERP systems</p>
</div>
""", unsafe_allow_html=True)

df: pd.DataFrame = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("No data available. Run pipeline_runner.py to ingest data from source systems.")
    st.stop()

# ── KPI Cards ──────────────────────────────────────────────────────────────────
total_incidents = len(df)
total_credit    = df["credit_requested_usd"].sum()
n_plants        = df["plant"].nunique()
n_customers     = df["customer"].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Total Incidents</div>
        <div class="kpi-value">{total_incidents:,}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Total Credits Requested (USD)</div>
        <div class="kpi-value green">${total_credit:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="kpi-card yellow">
        <div class="kpi-label">Plants Reporting</div>
        <div class="kpi-value yellow">{n_plants}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="kpi-card grey">
        <div class="kpi-label">Customers Affected</div>
        <div class="kpi-value">{n_customers}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Quarterly Stacked Bar ──────────────────────────────────────────────────────
st.markdown("#### Credit Requested by Quarter and Source System")
df_q = df.copy()
df_q["Quarter"] = df_q["incident_date"].dt.to_period("Q").astype(str)
q_pivot = df_q.groupby(["Quarter", "source"])["credit_requested_usd"].sum().reset_index()
q_pivot = q_pivot[q_pivot["Quarter"].notna() & (q_pivot["Quarter"] != "NaT")]

fig_bar = px.bar(
    q_pivot,
    x="Quarter",
    y="credit_requested_usd",
    color="source",
    labels={"credit_requested_usd": "Credit Requested (USD)", "source": "Source System"},
    color_discrete_sequence=PALETTE,
    template="plotly_white",
)
fig_bar.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11)),
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter", color=MCC_DARK),
    margin=dict(l=0, r=0, t=40, b=0),
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #E0E6EF;margin:8px 0 20px 0'>",
            unsafe_allow_html=True)

# ── Side-by-side: Source summary + Monthly trend ───────────────────────────────
col_a, col_b = st.columns([1, 1.6])

with col_a:
    st.markdown("#### By Source System")
    src_agg = df.groupby("source").agg(
        Incidents=("source", "count"),
        Credits_USD=("credit_requested_usd", "sum"),
    ).reset_index().sort_values("Credits_USD", ascending=False)
    src_agg["Credits_USD"] = src_agg["Credits_USD"].apply(lambda x: f"${x:,.0f}")
    src_agg.columns = ["Source System", "Incidents", "Total Credits (USD)"]
    st.dataframe(src_agg, use_container_width=True, hide_index=True)

with col_b:
    st.markdown("#### Monthly Credit Trend")
    df_m = df.copy()
    df_m["Month"] = df_m["incident_date"].dt.to_period("M").astype(str)
    monthly = df_m.groupby("Month").agg(
        Incidents=("source", "count"),
        Credits=("credit_requested_usd", "sum"),
    ).reset_index().sort_values("Month")
    monthly = monthly[monthly["Month"] != "NaT"]

    fig_line = px.line(
        monthly,
        x="Month",
        y="Credits",
        markers=True,
        template="plotly_white",
        labels={"Credits": "Credit Requested (USD)", "Month": ""},
        color_discrete_sequence=[MCC_BLUE],
    )
    fig_line.update_traces(line_width=2.5, marker_size=7)
    fig_line.update_layout(
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter", color=MCC_DARK),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_line, use_container_width=True)
