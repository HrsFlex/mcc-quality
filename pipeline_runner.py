"""
pipeline_runner.py — Main orchestrator for the Quality Data Pipeline.

Execution order:
  1. Auto-detect latest source files via file_detector
  2. Load raw data via per-source connectors
  3. Normalise to unified schema
  4. Validate & clean
  5. Upsert into SQLite (quality_incidents table)
  6. Check high-credit alerts
  7. Generate weekly Excel report
  8. Return open DB connection (so caller can build emails, etc.)

Run manually:
    python pipeline_runner.py
    python pipeline_runner.py --report-only   # Skip ingestion, only regenerate report
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# ── Path bootstrap so sub-modules import correctly ─────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline_runner")


def run_pipeline(report_only: bool = False):
    """
    Full pipeline execution. Returns the open SQLite connection on success,
    or None on catastrophic failure.
    """
    run_id     = str(uuid4())
    started_at = datetime.now(timezone.utc)
    logger.info(f"{'='*60}")
    logger.info(f"Pipeline run started  — run_id: {run_id}")
    logger.info(f"{'='*60}")

    # ── Step 1: Init DB ────────────────────────────────────────────────────────
    from repository.db import init_db
    conn = init_db()

    if report_only:
        logger.info("--report-only flag set — skipping ingestion, generating report only.")
        from reports.weekly_summary import generate
        os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
        generate(conn, cfg.OUTPUT_DIR, run_id)
        return conn

    # ── Step 2: Detect source files ────────────────────────────────────────────
    from connectors.file_detector import detect_source_files
    source_files = detect_source_files(cfg.DATA_DIR, cfg.SOURCE_PATTERNS)
    sources_loaded = [k for k, v in source_files.items() if v]
    logger.info(f"Detected sources: {sources_loaded}")

    if not sources_loaded:
        logger.error("No source files found — aborting pipeline run.")
        return None

    # ── Step 3: Load raw data via connectors ───────────────────────────────────
    from connectors.radius_connector  import RadiusConnector
    from connectors.fusion_connector  import FusionConnector
    from connectors.vision_connector  import VisionConnector
    from connectors.obi_connector     import OBIConnector

    raw_frames = {}
    connector_map = {
        "Radius":     lambda p: RadiusConnector(p).load(),
        "Fusion":     lambda p: FusionConnector(p).load(),
        "Vision_OAK": lambda p: VisionConnector(p, plant_tag="OAK").load(),
        "Vision_MAS": lambda p: VisionConnector(p, plant_tag="MAS").load(),
        "OBI":        lambda p: OBIConnector(p).load(),
    }

    for key, fpath in source_files.items():
        if not fpath:
            continue
        try:
            loader_fn = connector_map.get(key)
            if loader_fn:
                df = loader_fn(fpath)
                raw_frames[key] = (df, fpath)
                logger.info(f"Loaded {key}: {len(df)} rows from {os.path.basename(fpath)}")
        except Exception as e:
            logger.error(f"Failed to load {key} from {fpath}: {e}", exc_info=True)

    if not raw_frames:
        logger.error("All connectors failed — aborting.")
        return None

    # ── Step 4: Normalise ──────────────────────────────────────────────────────
    from transform.normalizer import normalize
    unified = normalize(raw_frames, run_id, fx_rates=cfg.FX_RATES)

    # ── Step 5: Validate ───────────────────────────────────────────────────────
    from transform.validator import validate
    clean = validate(unified)

    if clean.empty:
        logger.error("No valid rows after validation — aborting.")
        return None

    # ── Step 6: Load into DB ───────────────────────────────────────────────────
    from repository.loader import load
    n_rows = load(
        conn,
        df=clean,
        run_id=run_id,
        started_at=started_at,
        sources_loaded=sources_loaded,
        risk_tiers=cfg.RISK_TIERS,
    )

    # ── Step 7: High-credit alerts ─────────────────────────────────────────────
    threshold = cfg.ALERT_THRESHOLDS["single_incident_usd"]
    high_credit = clean[clean["credit_requested_usd"] >= threshold]
    if not high_credit.empty:
        from alerts.email_sender import send_high_credit_alert
        logger.warning(f"Found {len(high_credit)} high-credit incidents (≥ ${threshold:,})")
        for _, row in high_credit.iterrows():
            send_high_credit_alert(row.to_dict(), cfg)

    # ── Step 8: Generate Excel report ─────────────────────────────────────────
    from reports.weekly_summary import generate
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    report_path = generate(conn, cfg.OUTPUT_DIR, run_id)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline run complete — {n_rows} rows loaded, report: {report_path}")
    logger.info(f"{'='*60}")

    return conn


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quality Data Pipeline Runner")
    parser.add_argument("--report-only", action="store_true",
                        help="Skip ingestion; only regenerate Excel report from existing DB")
    args = parser.parse_args()

    conn = run_pipeline(report_only=args.report_only)
    if conn:
        conn.close()
