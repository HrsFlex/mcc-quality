"""
email_sender.py — Builds and either sends or dry-runs the alert/summary email.
DRY RUN (default): Saves the HTML email body to disk in outputs/email_drafts/.
LIVE mode: Set EMAIL_DRY_RUN=False in config.py and fill SMTP credentials.
"""
import os
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _build_html(subject: str, headline: str, kpi_rows: list, detail_rows: list) -> str:
    """
    Build an HTML email body.
    kpi_rows: list of (label, value) tuples for the top KPI section.
    detail_rows: list of (label, value) tuples for the detail table.
    """
    kpi_html = "".join(
        f"<td style='padding:12px 20px;text-align:center;'>"
        f"<div style='font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px'>{lbl}</div>"
        f"<div style='font-size:22px;font-weight:700;color:#003366'>{val}</div></td>"
        for lbl, val in kpi_rows
    )
    detail_html = "".join(
        f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eee;color:#555'>{lbl}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eee;font-weight:600'>{val}</td></tr>"
        for lbl, val in detail_rows
    )
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;padding:20px;margin:0">
  <div style="max-width:700px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;
              box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <div style="background:#003366;padding:24px 30px">
      <h1 style="margin:0;color:#fff;font-size:20px">📊 {headline}</h1>
      <p style="margin:4px 0 0;color:#a0b8d8;font-size:13px">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div style="padding:20px 30px">
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
        <tr>{kpi_html}</tr>
      </table>
      <h3 style="color:#003366;margin-bottom:8px">Details</h3>
      <table style="width:100%;border-collapse:collapse">
        {detail_html}
      </table>
    </div>
    <div style="background:#f5f7fa;padding:12px 30px;font-size:11px;color:#aaa">
      Quality Data Pipeline • Automated Report
    </div>
  </div>
</body>
</html>
"""


def _save_dry_run(html: str, subject: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{subject[:40].replace(' ', '_')}.html"
    fpath = os.path.join(out_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"[Email] DRY-RUN: HTML saved → {fpath}")
    return fpath


def _send_smtp(html: str, subject: str, recipients: list, cfg: dict):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = cfg["from_addr"]
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["from_addr"], recipients, msg.as_string())
    logger.info(f"[Email] Sent to {recipients}")


def send_alert(
    subject: str,
    headline: str,
    kpi_rows: list,
    detail_rows: list,
    recipients: list,
    dry_run: bool,
    dry_run_dir: str,
    smtp_cfg: dict = None,
):
    html = _build_html(subject, headline, kpi_rows, detail_rows)
    if dry_run or not smtp_cfg:
        return _save_dry_run(html, subject, dry_run_dir)
    else:
        _send_smtp(html, subject, recipients, smtp_cfg)
        return None


# ── Pre-built alert templates ─────────────────────────────────────────────────

def send_weekly_summary_email(conn, cfg_module):
    """Build and dispatch the weekly quality summary email."""
    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM quality_incidents", conn)
    total_incidents = len(df)
    total_credit    = df["credit_requested_usd"].sum()
    top_plant       = df.groupby("plant")["credit_requested_usd"].sum().idxmax() if not df.empty else "N/A"
    top_customer    = df.groupby("customer")["credit_requested_usd"].sum().idxmax() if not df.empty else "N/A"

    kpi_rows = [
        ("Total Incidents", f"{total_incidents:,}"),
        ("Total Credits (USD)", f"${total_credit:,.0f}"),
        ("Top Plant", top_plant),
        ("Top Customer", top_customer),
    ]
    detail_rows = [
        ("Data Sources Active", ", ".join(df["source"].unique().tolist())),
        ("Plants Reporting",    str(df["plant"].nunique())),
        ("Customers Affected",  str(df["customer"].nunique())),
    ]

    send_alert(
        subject="Weekly Quality Summary",
        headline="Weekly Quality Insights",
        kpi_rows=kpi_rows,
        detail_rows=detail_rows,
        recipients=cfg_module.EMAIL_RECIPIENTS,
        dry_run=cfg_module.EMAIL_DRY_RUN,
        dry_run_dir=cfg_module.EMAIL_HTML_OUT_DIR,
        smtp_cfg={
            "host": cfg_module.SMTP_HOST, "port": cfg_module.SMTP_PORT,
            "user": cfg_module.SMTP_USER, "password": cfg_module.SMTP_PASSWORD,
            "from_addr": cfg_module.EMAIL_FROM,
        },
    )


def send_high_credit_alert(incident_row: dict, cfg_module):
    """Immediate alert when a single incident exceeds the credit threshold."""
    kpi_rows = [
        ("Credit (USD)", f"${incident_row.get('credit_requested_usd', 0):,.0f}"),
        ("Plant",        incident_row.get("plant", "Unknown")),
        ("Customer",     incident_row.get("customer", "Unknown")),
    ]
    detail_rows = [
        ("Defect Category", incident_row.get("defect_category", "Unknown")),
        ("Incident Date",   str(incident_row.get("incident_date", ""))),
        ("Source System",   incident_row.get("source", "Unknown")),
    ]
    send_alert(
        subject="⚠️ High Credit Alert",
        headline="High Credit Quality Incident Detected",
        kpi_rows=kpi_rows,
        detail_rows=detail_rows,
        recipients=cfg_module.EMAIL_RECIPIENTS,
        dry_run=cfg_module.EMAIL_DRY_RUN,
        dry_run_dir=cfg_module.EMAIL_HTML_OUT_DIR,
        smtp_cfg={
            "host": cfg_module.SMTP_HOST, "port": cfg_module.SMTP_PORT,
            "user": cfg_module.SMTP_USER, "password": cfg_module.SMTP_PASSWORD,
            "from_addr": cfg_module.EMAIL_FROM,
        },
    )
