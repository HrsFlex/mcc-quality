"""
test_repository.py — Integration tests for db init, loader upsert, and run log.
Uses an in-memory SQLite database so no files are created.
"""
import sys, os
import sqlite3
import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_conn():
    """In-memory SQLite connection with schema applied."""
    # Patch DB_PATH so init_db() uses :memory:
    with patch("config.DB_PATH", ":memory:"), \
         patch("config.USE_SNOWFLAKE", False):
        import importlib
        import repository.db as db_mod
        importlib.reload(db_mod)
        conn = db_mod.init_db()
    yield conn
    conn.close()


def _sample_df(n=3, run_id="test-run"):
    return pd.DataFrame([
        {
            "pipeline_run_id": run_id,
            "source": "Fusion (Rochester)",
            "plant": "Rochester",
            "customer": f"Customer {i}",
            "incident_date": pd.Timestamp("2025-06-10"),
            "defect_category": "Sticking",
            "credit_requested_usd": 1000.0 * i,
            "qty_affected": 100.0 * i,
            "raw_source_file": "fake.xlsx",
        }
        for i in range(1, n + 1)
    ])


def test_db_tables_created(mem_conn):
    cur = mem_conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    assert "quality_incidents" in tables
    assert "pipeline_run_log" in tables
    assert "dim_plant" in tables


def test_loader_inserts_rows(mem_conn):
    from repository.loader import load
    df = _sample_df(3, run_id="run-001")
    n = load(
        mem_conn, df,
        run_id="run-001",
        started_at=datetime.now(timezone.utc),
        sources_loaded=["Fusion"],
        risk_tiers={"High": 100_000, "Medium": 30_000, "Low": 0},
    )
    assert n == 3
    cur = mem_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM quality_incidents")
    assert cur.fetchone()[0] == 3


def test_loader_idempotent(mem_conn):
    """Re-inserting same run_id rows should not create duplicates."""
    from repository.loader import load
    df = _sample_df(3, run_id="run-dup")
    load(mem_conn, df, run_id="run-dup",
         started_at=datetime.now(timezone.utc),
         sources_loaded=["Fusion"],
         risk_tiers={"High": 100_000, "Medium": 30_000, "Low": 0})
    load(mem_conn, df, run_id="run-dup",
         started_at=datetime.now(timezone.utc),
         sources_loaded=["Fusion"],
         risk_tiers={"High": 100_000, "Medium": 30_000, "Low": 0})
    cur = mem_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM quality_incidents WHERE pipeline_run_id='run-dup'")
    assert cur.fetchone()[0] == 3   # still 3, not 6


def test_run_log_written(mem_conn):
    from repository.loader import load
    df = _sample_df(2, run_id="run-log-test")
    load(mem_conn, df, run_id="run-log-test",
         started_at=datetime.now(timezone.utc),
         sources_loaded=["Fusion", "Radius"],
         risk_tiers={"High": 100_000, "Medium": 30_000, "Low": 0})
    cur = mem_conn.cursor()
    cur.execute("SELECT status, total_rows FROM pipeline_run_log WHERE run_id='run-log-test'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "SUCCESS"
    assert row[1] == 2
