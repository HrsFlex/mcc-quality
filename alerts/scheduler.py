"""
scheduler.py — APScheduler-based automation layer.
Runs the pipeline on schedule AND supports the file-watcher trigger.

Jobs:
  1. Weekly pipeline run every Monday 08:00 (full ETL + report + email)
  2. Monthly scorecard email on the 1st of each month at 09:00
  3. File-watcher polling (configurable interval) for on-drop auto-runs

Usage:
    python scheduler.py              # Runs scheduler + watcher indefinitely
    python scheduler.py --once       # One immediate pipeline run then exit
"""
import argparse
import logging
import sys
import os

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_root = os.path.dirname(os.path.abspath(__file__))
_pkg  = os.path.dirname(_root)
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import config as cfg
from pipeline_runner import run_pipeline
from connectors.file_detector import FileWatcher
from alerts.email_sender import send_weekly_summary_email
from repository.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler")


def _weekly_job():
    logger.info("=== SCHEDULED WEEKLY RUN ===")
    conn = run_pipeline()
    if conn:
        send_weekly_summary_email(conn, cfg)
        conn.close()


def _monthly_job():
    logger.info("=== SCHEDULED MONTHLY SCORECARD ===")
    conn = get_connection()
    send_weekly_summary_email(conn, cfg)   # reuse same template; can be customised
    conn.close()


def start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        raise RuntimeError("apscheduler not installed. Run: pip install apscheduler")

    scheduler = BackgroundScheduler()

    # Weekly pipeline run (Monday 08:00)
    scheduler.add_job(
        _weekly_job,
        trigger="cron",
        day_of_week=cfg.SCHEDULE_WEEKLY_DAY,
        hour=cfg.SCHEDULE_WEEKLY_HOUR,
        minute=0,
        id="weekly_pipeline",
        name="Weekly Pipeline Run",
        replace_existing=True,
    )

    # Monthly scorecard (1st of month 09:00)
    scheduler.add_job(
        _monthly_job,
        trigger="cron",
        day=cfg.SCHEDULE_MONTHLY_DAY,
        hour=cfg.SCHEDULE_MONTHLY_HOUR,
        minute=0,
        id="monthly_scorecard",
        name="Monthly Scorecard Email",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started — weekly on {cfg.SCHEDULE_WEEKLY_DAY.upper()} "
        f"@ {cfg.SCHEDULE_WEEKLY_HOUR:02d}:00, "
        f"monthly on day {cfg.SCHEDULE_MONTHLY_DAY} @ {cfg.SCHEDULE_MONTHLY_HOUR:02d}:00"
    )
    return scheduler


def start_file_watcher():
    watcher = FileWatcher(
        data_dir=cfg.DATA_DIR,
        source_patterns=cfg.SOURCE_PATTERNS,
    )
    logger.info(f"File-watcher started — polling every {cfg.WATCHER_POLL_INTERVAL_SEC}s")
    watcher.run_forever(
        callback=lambda: run_pipeline(),
        poll_interval_sec=cfg.WATCHER_POLL_INTERVAL_SEC,
    )


def main():
    parser = argparse.ArgumentParser(description="Quality Pipeline Scheduler")
    parser.add_argument("--once", action="store_true",
                        help="Run pipeline once immediately and exit")
    parser.add_argument("--watcher-only", action="store_true",
                        help="Only run file watcher, skip APScheduler")
    args = parser.parse_args()

    if args.once:
        logger.info("Running pipeline once ...")
        run_pipeline()
        return

    # Start APScheduler in background thread
    if not args.watcher_only:
        scheduler = start_scheduler()

    # Block on file watcher (this is the main thread)
    try:
        start_file_watcher()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
        if not args.watcher_only:
            scheduler.shutdown()


if __name__ == "__main__":
    main()
