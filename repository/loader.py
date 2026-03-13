"""
loader.py — Upserts unified DataFrame rows into the quality_incidents table
and writes a summary row to pipeline_run_log.
"""
import logging
import sqlite3
from datetime import datetime, timezone
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def _upsert_incidents(conn: sqlite3.Connection, df: pd.DataFrame):
    """
    Insert all rows from the unified DataFrame into quality_incidents.
    On re-run with the same pipeline_run_id the table will contain the same
    rows (idempotent by virtue of run_id + incident_date + source).
    We use INSERT OR IGNORE with a unique index to prevent true duplicates.
    """
    cur = conn.cursor()

    # Unique index based on incident data only (NOT run_id).
    # This ensures re-running the pipeline with a new run_id never double-counts
    # the same real-world incident.
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_unique
        ON quality_incidents (source, plant, customer,
                              incident_date, defect_category,
                              ROUND(credit_requested_usd, 2));
    """)

    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute(
                """INSERT OR IGNORE INTO quality_incidents
                   (pipeline_run_id, source, plant, customer,
                    incident_date, defect_category,
                    credit_requested_usd, qty_affected, raw_source_file)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row.get("pipeline_run_id"),
                    row.get("source"),
                    row.get("plant"),
                    row.get("customer"),
                    str(row["incident_date"].date()) if pd.notna(row.get("incident_date")) else None,
                    row.get("defect_category"),
                    float(row.get("credit_requested_usd", 0) or 0),
                    float(row.get("qty_affected", 0) or 0),
                    row.get("raw_source_file"),
                ),
            )
            inserted += cur.rowcount
        except Exception as e:
            logger.warning(f"[Loader] Skipped row due to error: {e}")

    conn.commit()
    logger.info(f"[Loader] Inserted {inserted} new rows into quality_incidents")
    return inserted


def _update_customer_risk_tiers(conn: sqlite3.Connection, risk_tiers: dict):
    """Update dim_customer risk tier based on rolling credit totals."""
    cur = conn.cursor()
    cur.execute("""
        SELECT customer, SUM(credit_requested_usd) as total_credit
        FROM quality_incidents
        WHERE incident_date >= date('now', '-90 days')
        GROUP BY customer
    """)
    rows = cur.fetchall()
    for row in rows:
        customer, total = row["customer"], row["total_credit"] or 0
        if total >= risk_tiers.get("High", 100_000):
            tier = "High"
        elif total >= risk_tiers.get("Medium", 30_000):
            tier = "Medium"
        else:
            tier = "Low"
        cur.execute(
            """INSERT OR REPLACE INTO dim_customer (customer_name, risk_tier, updated_at)
               VALUES (?, ?, datetime('now'))""",
            (customer, tier),
        )
    conn.commit()
    logger.info("[Loader] Customer risk tiers updated")


def write_run_log(
    conn: sqlite3.Connection,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    total_rows: int,
    sources_loaded: List[str],
    error_message: str = "",
):
    cur = conn.cursor()
    cur.execute(
        """INSERT OR REPLACE INTO pipeline_run_log
           (run_id, started_at, finished_at, status, total_rows, sources_loaded, error_message)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            started_at.isoformat(),
            finished_at.isoformat(),
            status,
            total_rows,
            ",".join(sources_loaded),
            error_message,
        ),
    )
    conn.commit()
    logger.info(f"[Loader] Run log written: {run_id} → {status} ({total_rows} rows)")


def load(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    run_id: str,
    started_at: datetime,
    sources_loaded: List[str],
    risk_tiers: dict,
):
    """
    Main entry point: upsert incidents, update risk tiers, write run log.
    """
    status = "SUCCESS"
    error_message = ""
    total_rows = 0
    try:
        total_rows = _upsert_incidents(conn, df)
        _update_customer_risk_tiers(conn, risk_tiers)
    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        logger.error(f"[Loader] Load failed: {e}", exc_info=True)

    write_run_log(
        conn,
        run_id=run_id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        status=status,
        total_rows=total_rows,
        sources_loaded=sources_loaded,
        error_message=error_message,
    )
    return total_rows
