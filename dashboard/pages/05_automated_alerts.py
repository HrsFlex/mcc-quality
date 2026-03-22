"""
05_automated_alerts.py — Automated Alerts & Insights
"""
import os
import sys
import pandas as pd
import streamlit as st

# MCC Brand Colors
MCC_BLUE   = "#6DB0E2"
MCC_GREEN  = "#2FAC67"
MCC_YELLOW = "#FED742"
MCC_DARK   = "#1A1A2E"
MCC_GREY   = "#5C6272"

st.markdown("""
<div class="page-header">
  <h2>Automated Quality Alerts</h2>
  <p>Real-time detection of critical incidents, repeat offenders, and weekly operational summaries</p>
</div>
""", unsafe_allow_html=True)

df: pd.DataFrame = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("No data available.")
    st.stop()

# Load config to get thresholds
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))
if _root not in sys.path:
    sys.path.insert(0, _root)
import config as cfg

threshold_usd = cfg.ALERT_THRESHOLDS.get("single_incident_usd", 10000)

tabs = st.tabs(["🔴 High-Value Alerts", "🔄 Repeat Customers", "📅 Weekly Summary"])

# ── 1. High-value memos ────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown(f"### High-Value Incidents (≥ ${threshold_usd:,})")
    st.caption("Incidents exceeding financial thresholds that require immediate leadership review.")
    
    high_value_df = df[df["credit_requested_usd"] >= threshold_usd].copy()
    if not high_value_df.empty:
        high_value_df = high_value_df.sort_values("credit_requested_usd", ascending=False)
        cols_to_show = ["incident_date", "source", "customer", "plant", "credit_requested_usd", "defect_category", "status"]
        # Ensure columns exist
        cols_to_show = [c for c in cols_to_show if c in high_value_df.columns]
        
        # Format the USD column
        display_df = high_value_df[cols_to_show].copy()
        if "credit_requested_usd" in display_df.columns:
            display_df["credit_requested_usd"] = display_df["credit_requested_usd"].apply(lambda x: f"${x:,.2f}")
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.success(f"No high-value incidents exceeding ${threshold_usd:,} found in the current date range.")

# ── 2. Repeat customer memos ───────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### Repeat Customer Alerts (Monthly)")
    st.caption("Customers with multiple quality incidents within the same calendar month.")
    
    rc_df = df.copy()
    rc_df["Month"] = rc_df["incident_date"].dt.to_period("M")
    
    # Group by Customer and Month
    if "customer" in rc_df.columns:
        repeat_counts = rc_df.groupby(["customer", "Month"]).size().reset_index(name="Incident Count")
        repeat_counts = repeat_counts[repeat_counts["Incident Count"] > 1]
        
        if not repeat_counts.empty:
            repeat_counts = repeat_counts.sort_values("Incident Count", ascending=False)
            repeat_counts["Month"] = repeat_counts["Month"].astype(str)
            st.dataframe(repeat_counts, use_container_width=True, hide_index=True)
        else:
            st.success("No chronic repeat incidents for the same customer within a single month found.")
    else:
        st.warning("Customer data not available.")

# ── 3. Weekly Summary ──────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### Weekly Operational Summary")
    st.caption("Aggregated view of incident volume and financial impact grouped by week.")
    
    ws_df = df.copy()
    # Group by week using string format
    ws_df["Week_Start"] = ws_df["incident_date"].dt.to_period("W").apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
    
    weekly_agg = ws_df.groupby("Week_Start").agg(
        Total_Incidents=("source", "count"),
        Total_Credit_USD=("credit_requested_usd", "sum"),
        Unique_Plants=("plant", "nunique"),
        Unique_Customers=("customer", "nunique")
    ).reset_index().sort_values("Week_Start", ascending=False)
    
    weekly_agg["Total_Credit_USD"] = weekly_agg["Total_Credit_USD"].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(weekly_agg, use_container_width=True, hide_index=True)
    
    # Check if a weekly report exists in the output dir
    report_path = os.path.join(cfg.OUTPUT_DIR, "weekly_quality_report.xlsx")
    if os.path.exists(report_path):
        st.markdown("<hr style='border:none;border-top:1px solid #E0E6EF;margin:16px 0;'>", unsafe_allow_html=True)
        st.markdown("#### Download Full Report")
        with open(report_path, "rb") as f:
            st.download_button(
                label="📥 Download Weekly Excel Summary",
                data=f,
                file_name="weekly_quality_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
