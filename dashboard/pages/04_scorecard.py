"""
04_scorecard.py — Customer Quality Scorecard — MCC Label Solutions
"""
import pandas as pd
import plotly.express as px
import streamlit as st
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _root not in sys.path:
    sys.path.insert(0, _root)
import config as cfg

MCC_BLUE   = "#6DB0E2"
MCC_GREEN  = "#2FAC67"
MCC_YELLOW = "#FED742"
MCC_DARK   = "#1A1A2E"

# Risk tier colors — accessible on white background
TIER_COLORS = {
    "High":   "#C0392B",   # Deep red
    "Medium": "#C9A200",   # Darkened yellow for contrast
    "Low":    "#2FAC67",   # MCC Green
}

st.markdown("""
<div class="page-header">
  <h2>Customer Quality Scorecard</h2>
  <p>Per-customer risk classification, cumulative credit totals, and primary defect drivers</p>
</div>
""", unsafe_allow_html=True)

df: pd.DataFrame = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("No data available.")
    st.stop()

# ── Build scorecard ────────────────────────────────────────────────────────────
scorecard = (
    df.groupby("customer")
    .agg(
        Incidents=("customer", "count"),
        Total_Credit_USD=("credit_requested_usd", "sum"),
        Avg_Credit_USD=("credit_requested_usd", "mean"),
        Max_Credit_USD=("credit_requested_usd", "max"),
        Top_Defect=("defect_category",
                    lambda x: x.value_counts().index[0] if len(x) else "N/A"),
        Sources=("source", lambda x: ", ".join(sorted(x.unique()))),
        Plants=("plant", "nunique"),
    )
    .reset_index()
    .sort_values("Total_Credit_USD", ascending=False)
)

def _assign_tier(total: float) -> str:
    if total >= cfg.RISK_TIERS["High"]:   return "High"
    if total >= cfg.RISK_TIERS["Medium"]: return "Medium"
    return "Low"

scorecard["Risk Tier"] = scorecard["Total_Credit_USD"].apply(_assign_tier)

# ── Risk summary ───────────────────────────────────────────────────────────────
high_count = (scorecard["Risk Tier"] == "High").sum()
med_count  = (scorecard["Risk Tier"] == "Medium").sum()
low_count  = (scorecard["Risk Tier"] == "Low").sum()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#C0392B">
        <div class="kpi-label">High Risk Customers</div>
        <div class="kpi-value" style="color:#C0392B">{high_count}</div>
        <div class="kpi-sub">Credit total &gt; ${cfg.RISK_TIERS['High']:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card yellow">
        <div class="kpi-label">Medium Risk Customers</div>
        <div class="kpi-value yellow">{med_count}</div>
        <div class="kpi-sub">Credit total ${cfg.RISK_TIERS['Medium']:,.0f} – ${cfg.RISK_TIERS['High']:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Low Risk Customers</div>
        <div class="kpi-value green">{low_count}</div>
        <div class="kpi-sub">Credit total &lt; ${cfg.RISK_TIERS['Medium']:,.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Risk tier filter ───────────────────────────────────────────────────────────
tier_filter = st.multiselect(
    "Filter by Risk Classification",
    ["High", "Medium", "Low"],
    default=["High", "Medium", "Low"],
)
sc_filtered = scorecard[scorecard["Risk Tier"].isin(tier_filter)]

# ── Horizontal bar chart ───────────────────────────────────────────────────────
st.markdown(f"#### Top {cfg.TOP_N_CUSTOMERS} Customers by Total Credit Requested")
top_sc = sc_filtered.head(cfg.TOP_N_CUSTOMERS)

fig = px.bar(
    top_sc.sort_values("Total_Credit_USD"),
    x="Total_Credit_USD",
    y="customer",
    color="Risk Tier",
    color_discrete_map=TIER_COLORS,
    orientation="h",
    template="plotly_white",
    labels={
        "Total_Credit_USD": "Total Credit Requested (USD)",
        "customer": "Customer",
        "Risk Tier": "Risk Classification",
    },
    hover_data=["Incidents", "Top_Defect"],
)
fig.update_layout(
    xaxis_tickprefix="$",
    xaxis_tickformat=",.0f",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter", color=MCC_DARK, size=11),
    legend=dict(title="Risk Classification", orientation="h", y=1.05),
    margin=dict(l=0, r=0, t=40, b=0),
)
st.plotly_chart(fig, use_container_width=True)

# ── Full scorecard table ───────────────────────────────────────────────────────
st.markdown("#### Full Customer Scorecard")

display = sc_filtered[[
    "Risk Tier", "customer", "Incidents",
    "Total_Credit_USD", "Avg_Credit_USD", "Max_Credit_USD",
    "Top_Defect", "Plants", "Sources",
]].copy()
display.columns = [
    "Risk Classification", "Customer", "Incidents",
    "Total Credit (USD)", "Avg Credit (USD)", "Max Credit (USD)",
    "Primary Defect Type", "No. of Plants", "Source Systems",
]
for col in ["Total Credit (USD)", "Avg Credit (USD)", "Max Credit (USD)"]:
    display[col] = display[col].apply(lambda x: f"${x:,.0f}")

st.dataframe(display, use_container_width=True, hide_index=True)

csv = sc_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Scorecard as CSV",
    csv,
    "mcc_customer_scorecard.csv",
    "text/csv",
)
