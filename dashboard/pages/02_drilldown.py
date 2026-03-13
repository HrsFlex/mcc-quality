"""
02_drilldown.py — Incident Detail — MCC Label Solutions
"""
import pandas as pd
import plotly.express as px
import streamlit as st

MCC_BLUE   = "#6DB0E2"
MCC_GREEN  = "#2FAC67"
MCC_YELLOW = "#FED742"
MCC_DARK   = "#1A1A2E"
PALETTE    = [MCC_BLUE, MCC_GREEN, "#C9A200", "#4a9dd4", "#259958"]

st.markdown("""
<div class="page-header">
  <h2>Incident Detail</h2>
  <p>Filter and examine individual quality incidents across any dimension</p>
</div>
""", unsafe_allow_html=True)

df: pd.DataFrame = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("No data available.")
    st.stop()

# ── Additional page-level filters ─────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    all_customers = ["All"] + sorted(df["customer"].dropna().unique().tolist())
    sel_cust = st.selectbox("Customer", all_customers)
with col2:
    all_defects = ["All"] + sorted(df["defect_category"].dropna().unique().tolist())
    sel_defect = st.selectbox("Defect Category", all_defects)
with col3:
    min_credit = st.number_input("Minimum Credit Amount (USD)", min_value=0.0,
                                  value=0.0, step=1000.0)

dff = df.copy()
if sel_cust   != "All": dff = dff[dff["customer"] == sel_cust]
if sel_defect != "All": dff = dff[dff["defect_category"] == sel_defect]
if min_credit > 0:       dff = dff[dff["credit_requested_usd"] >= min_credit]

# ── Summary stats ──────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Incidents in Current View", f"{len(dff):,}")
c2.metric("Total Credits (USD)",        f"${dff['credit_requested_usd'].sum():,.0f}")
c3.metric("Average Credit per Incident",
          f"${dff['credit_requested_usd'].mean():,.0f}" if len(dff) else "$0")

st.markdown("<br>", unsafe_allow_html=True)

# ── Trend chart ────────────────────────────────────────────────────────────────
st.markdown("#### Credit Trend — Filtered View")
dff_m = dff.copy()
dff_m["Month"] = dff_m["incident_date"].dt.to_period("M").astype(str)
monthly = dff_m.groupby(["Month", "source"])["credit_requested_usd"].sum().reset_index()
monthly = monthly[monthly["Month"] != "NaT"]

if not monthly.empty:
    fig = px.area(
        monthly,
        x="Month",
        y="credit_requested_usd",
        color="source",
        template="plotly_white",
        labels={"credit_requested_usd": "Credit Requested (USD)", "source": "Source System"},
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter", color=MCC_DARK),
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Data table ─────────────────────────────────────────────────────────────────
st.markdown(f"#### Incident Records &nbsp;&nbsp;<span style='font-size:13px;color:#5C6272;font-weight:400'>{len(dff):,} records</span>",
            unsafe_allow_html=True)

display_cols = ["incident_date", "source", "plant", "customer",
                "defect_category", "credit_requested_usd", "qty_affected"]
available = [c for c in display_cols if c in dff.columns]
col_labels = {
    "incident_date":        "Incident Date",
    "source":               "Source System",
    "plant":                "Plant",
    "customer":             "Customer",
    "defect_category":      "Defect Category",
    "credit_requested_usd": "Credit Requested (USD)",
    "qty_affected":         "Quantity Affected",
}
display_df = (dff[available]
              .rename(columns=col_labels)
              .sort_values("Credit Requested (USD)", ascending=False))

st.dataframe(display_df, use_container_width=True, hide_index=True)

csv = dff[available].to_csv(index=False).encode("utf-8")
st.download_button("Download as CSV", csv, "mcc_quality_incidents.csv", "text/csv")
