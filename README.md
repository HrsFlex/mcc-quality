# MCC Quality Insights Dashboard

Enterprise quality performance dashboard prepared by **Blend** for **MCC Label Solutions**.

## Overview

A multi-source quality data pipeline and interactive dashboard that ingests, transforms, and visualises quality incidents across all MCC plants and ERP systems (Radius, Fusion, Vision, OBI).

## Dashboard Pages

| Page | Description |
|---|---|
| Overview | Enterprise KPIs, quarterly trends by source, monthly credit trend |
| Incident Detail | Filterable drill-down into individual incidents with CSV export |
| Root Cause Analysis | Pareto analysis and plant/customer heatmaps |
| Customer Scorecard | Risk classification (High/Medium/Low) with credit totals |

## Running Locally

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Pipeline Automation

```bash
# Full ETL run (detects latest source files automatically)
python pipeline_runner.py

# Continuous mode — file watcher + scheduled weekly/monthly runs
python alerts/scheduler.py
```

## Technology

- **Streamlit** — interactive dashboard
- **SQLite** — local data store (Snowflake migration path documented)
- **Plotly** — charts and heatmaps
- **APScheduler** — weekly/monthly automation

---

*Prepared by Blend for MCC Label Solutions — Confidential*
