"""
config.py — Central configuration for the Quality Data Pipeline.
Adjust paths, thresholds, and credentials here before running.
"""

import os
from pathlib import Path

# ─── Directories ───────────────────────────────────────────────────────────────
# All paths are relative to this config file so the app runs anywhere:
# locally on Windows AND on Streamlit Cloud.
PIPELINE_DIR = Path(__file__).parent.resolve()          # quality_pipeline/
BASE_DIR     = PIPELINE_DIR.parent                      # chrunModeling/
DATA_DIR     = BASE_DIR / "Fw_ Quality Data"            # raw source files (local only)
OUTPUT_DIR   = PIPELINE_DIR / "outputs"                 # Excel reports, HTML emails
DB_PATH      = str(PIPELINE_DIR / "quality.db")         # SQLite database

# ─── Source File Patterns (glob) ───────────────────────────────────────────────
# The pipeline will auto-detect the MOST RECENT file matching each pattern in DATA_DIR.
SOURCE_PATTERNS = {
    "Radius":     "*Radius*MDA*.xlsx",
    "Fusion":     "*Fusion*Quality*.xlsx",
    "Vision_OAK": "*Vision*OAK*.xlsx",
    "Vision_MAS": "*Vision*MAS*.xlsx",
    "OBI":        "*Feedback*Report*01QUALC009*.csv",   # CSV preferred
    "OBI_XLS":    "*Feedback*Report*01QUALC009*.xls",  # fallback
}

# ─── File Watcher ──────────────────────────────────────────────────────────────
# How often the watcher polls for new/modified files (seconds)
WATCHER_POLL_INTERVAL_SEC = 60

# ─── Database ──────────────────────────────────────────────────────────────────
USE_SNOWFLAKE = False   # Flip to True when Snowflake credentials are ready

SNOWFLAKE = {           # Ignored when USE_SNOWFLAKE = False
    "account":   os.environ.get("SF_ACCOUNT", ""),
    "user":      os.environ.get("SF_USER", ""),
    "password":  os.environ.get("SF_PASSWORD", ""),
    "database":  "QUALITY_DB",
    "schema":    "PUBLIC",
    "warehouse": "COMPUTE_WH",
}

# ─── Currency Conversion (to USD) ────────────────────────────────────────────
# Update rates as needed; these are applied by plant name.
FX_RATES = {
    "MCC Monterrey":  0.05,   # MXN → USD
    "MCC Guadalajara": 0.05,  # MXN → USD
    "MCC Montreal":   0.74,   # CAD → USD
}

# ─── Alert Thresholds ─────────────────────────────────────────────────────────
ALERT_THRESHOLDS = {
    "single_incident_usd": 50_000,   # Alert immediately if one incident > this
    "weekly_total_usd":   200_000,   # Alert if weekly total exceeds this
}

RISK_TIERS = {
    "High":   100_000,   # Customer total credits (USD) in rolling 90 days
    "Medium":  30_000,
    "Low":          0,
}

# ─── Email / Alerts (DRY-RUN: saves HTML to disk instead of sending) ──────────
EMAIL_DRY_RUN       = True          # Set False + fill creds below to actually send
EMAIL_RECIPIENTS    = ["quality-team@company.com"]
SMTP_HOST           = "smtp.office365.com"
SMTP_PORT           = 587
SMTP_USER           = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD       = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM          = "quality-pipeline@company.com"
EMAIL_HTML_OUT_DIR  = os.path.join(OUTPUT_DIR, "email_drafts")

# ─── Scheduler ────────────────────────────────────────────────────────────────
# APScheduler cron triggers
SCHEDULE_WEEKLY_DAY   = "mon"   # Weekly summary every Monday
SCHEDULE_WEEKLY_HOUR  = 8
SCHEDULE_MONTHLY_DAY  = 1       # Monthly scorecard on 1st of month
SCHEDULE_MONTHLY_HOUR = 9

# ─── Dashboard ────────────────────────────────────────────────────────────────
DASHBOARD_TITLE = "MCC Quality Insights Dashboard"
TOP_N_DEFECTS   = 10   # How many defect categories to show in Pareto/heatmap
TOP_N_CUSTOMERS = 15   # Rows in customer scorecard
