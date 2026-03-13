"""
03_root_cause.py — Root Cause Analysis — MCC Label Solutions
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

MCC_BLUE   = "#6DB0E2"
MCC_GREEN  = "#2FAC67"
MCC_YELLOW = "#FED742"
MCC_DARK   = "#1A1A2E"
PALETTE    = [MCC_BLUE, MCC_GREEN, "#C9A200", "#4a9dd4", "#259958", "#8ecae6", "#b5e48c"]

st.markdown("""
<div class="page-header">
  <h2>Root Cause Analysis</h2>
  <p>Pareto analysis of defect categories and cross-dimensional financial impact heatmaps</p>
</div>
""", unsafe_allow_html=True)

df: pd.DataFrame = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.info("No data available.")
    st.stop()

top_n = st.slider("Number of defect categories to display", min_value=5, max_value=20, value=10)

# ── Pareto Chart ───────────────────────────────────────────────────────────────
st.markdown("#### Pareto Analysis — Defect Categories by Financial Impact")

defect_agg = (
    df.groupby("defect_category")
    .agg(Incidents=("defect_category", "count"),
         Credit_USD=("credit_requested_usd", "sum"))
    .reset_index()
    .sort_values("Credit_USD", ascending=False)
    .head(top_n)
)
defect_agg["Cumulative %"] = (
    defect_agg["Credit_USD"].cumsum() / defect_agg["Credit_USD"].sum() * 100
)

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(
    x=defect_agg["defect_category"],
    y=defect_agg["Credit_USD"],
    name="Credit Requested (USD)",
    marker_color=MCC_BLUE,
    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
))
fig_pareto.add_trace(go.Scatter(
    x=defect_agg["defect_category"],
    y=defect_agg["Cumulative %"],
    name="Cumulative %",
    yaxis="y2",
    line=dict(color=MCC_GREEN, width=2.5),
    mode="lines+markers",
    marker=dict(size=7, color=MCC_GREEN),
))
fig_pareto.update_layout(
    yaxis=dict(title="Credit Requested (USD)", tickprefix="$", tickformat=",.0f",
               gridcolor="#E0E6EF"),
    yaxis2=dict(title="Cumulative %", overlaying="y", side="right",
                range=[0, 105], ticksuffix="%"),
    xaxis_tickangle=-35,
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter", color=MCC_DARK, size=11),
    legend=dict(orientation="h", y=1.10),
    margin=dict(l=0, r=0, t=50, b=80),
)
st.plotly_chart(fig_pareto, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #E0E6EF;margin:8px 0 20px 0'>",
            unsafe_allow_html=True)

# ── Heatmaps ──────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

top_defects = defect_agg["defect_category"].tolist()
top_plants  = (df.groupby("plant")["credit_requested_usd"].sum()
               .sort_values(ascending=False).head(10).index.tolist())
top_customers = (df.groupby("customer")["credit_requested_usd"].sum()
                 .sort_values(ascending=False).head(10).index.tolist())

with col_left:
    st.markdown("#### Plant by Defect Category")
    heat_pd = (
        df[df["defect_category"].isin(top_defects) & df["plant"].isin(top_plants)]
        .groupby(["plant", "defect_category"])["credit_requested_usd"].sum()
        .reset_index()
        .pivot(index="plant", columns="defect_category", values="credit_requested_usd")
        .fillna(0)
    )
    if not heat_pd.empty:
        fig_h1 = px.imshow(
            heat_pd.values,
            x=heat_pd.columns.tolist(),
            y=heat_pd.index.tolist(),
            color_continuous_scale=[[0, "#EBF5FB"], [0.5, MCC_BLUE], [1, "#1a5f8a"]],
            aspect="auto",
            labels=dict(color="Credit (USD)"),
            template="plotly_white",
        )
        fig_h1.update_xaxes(tickangle=-40, tickfont_size=9)
        fig_h1.update_layout(paper_bgcolor="#FFFFFF",
                              font=dict(family="Inter", color=MCC_DARK, size=10))
        st.plotly_chart(fig_h1, use_container_width=True)

with col_right:
    st.markdown("#### Customer by Defect Category")
    heat_cd = (
        df[df["defect_category"].isin(top_defects) & df["customer"].isin(top_customers)]
        .groupby(["customer", "defect_category"])["credit_requested_usd"].sum()
        .reset_index()
        .pivot(index="customer", columns="defect_category", values="credit_requested_usd")
        .fillna(0)
    )
    if not heat_cd.empty:
        fig_h2 = px.imshow(
            heat_cd.values,
            x=heat_cd.columns.tolist(),
            y=heat_cd.index.tolist(),
            color_continuous_scale=[[0, "#EAFAF1"], [0.5, MCC_GREEN], [1, "#1a6b40"]],
            aspect="auto",
            labels=dict(color="Credit (USD)"),
            template="plotly_white",
        )
        fig_h2.update_xaxes(tickangle=-40, tickfont_size=9)
        fig_h2.update_layout(paper_bgcolor="#FFFFFF",
                              font=dict(family="Inter", color=MCC_DARK, size=10))
        st.plotly_chart(fig_h2, use_container_width=True)

# ── Bivariate: Customer x Plant ───────────────────────────────────────────────
st.markdown("#### Customer and Plant Intersections — Top 15 by Credit")
biv = (
    df.groupby(["customer", "plant"])["credit_requested_usd"].sum()
    .reset_index()
    .sort_values("credit_requested_usd", ascending=False)
    .head(15)
)
biv["credit_requested_usd"] = biv["credit_requested_usd"].apply(lambda x: f"${x:,.0f}")
biv.columns = ["Customer", "Plant", "Total Credit (USD)"]
st.dataframe(biv, use_container_width=True, hide_index=True)
