"""
file_detector.py — Auto-detects the most recent source file per ERP system.
Uses glob patterns from config.py. Runs as a polling watcher so new files
dropped into DATA_DIR are automatically picked up on the next pipeline cycle.
"""
import glob
import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def find_latest_file(directory: str, pattern: str) -> Optional[str]:
    """
    Return the most recently modified file in `directory` matching `pattern`.
    Returns None if no file is found.
    """
    matches = glob.glob(os.path.join(directory, pattern))
    if not matches:
        return None
    # Sort by last-modified time descending; return newest
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def detect_source_files(data_dir: str, source_patterns: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Scan `data_dir` for each source pattern and return a dict:
      { source_key → latest_file_path_or_None }

    Special logic: OBI prefers CSV over XLS — if OBI CSV exists, OBI_XLS is suppressed.
    """
    results: Dict[str, Optional[str]] = {}
    for source_key, pattern in source_patterns.items():
        path = find_latest_file(data_dir, pattern)
        results[source_key] = path
        if path:
            logger.info(f"[FileDetector] {source_key}: {Path(path).name}")
        else:
            logger.warning(f"[FileDetector] {source_key}: No matching file found for pattern '{pattern}'")

    # OBI dedup: prefer CSV; if CSV found, drop XLS key
    if results.get("OBI") and results.get("OBI_XLS"):
        logger.info("[FileDetector] OBI CSV found — ignoring OBI_XLS fallback.")
        results.pop("OBI_XLS")
    elif not results.get("OBI") and results.get("OBI_XLS"):
        # Promote XLS to the OBI slot so downstream treats it as OBI
        results["OBI"] = results.pop("OBI_XLS")
        logger.info("[FileDetector] OBI CSV not found, falling back to OBI_XLS.")

    return results


class FileWatcher:
    """
    Polling-based file watcher. Tracks last-seen mtime for each source.
    Returns True from `has_new_files()` whenever any source file has been
    added or updated since the last check. Intended to be called in the
    scheduler loop.
    """

    def __init__(self, data_dir: str, source_patterns: Dict[str, str]):
        self.data_dir = data_dir
        self.source_patterns = source_patterns
        self._last_mtimes: Dict[str, float] = {}

    def _current_mtimes(self) -> Dict[str, float]:
        mtimes = {}
        for key, pattern in self.source_patterns.items():
            path = find_latest_file(self.data_dir, pattern)
            if path:
                mtimes[key] = os.path.getmtime(path)
        return mtimes

    def has_new_files(self) -> bool:
        """
        Returns True (and updates internal state) if any file is new or
        has been modified since the last call.
        """
        current = self._current_mtimes()
        changed = False
        for key, mtime in current.items():
            if self._last_mtimes.get(key) != mtime:
                logger.info(f"[FileWatcher] Change detected: {key}")
                changed = True
        self._last_mtimes = current
        return changed

    def run_forever(self, callback, poll_interval_sec: int = 60):
        """
        Block indefinitely, calling `callback()` whenever new/updated files
        are detected. `callback` should be the pipeline run function.
        """
        logger.info(f"[FileWatcher] Starting — polling every {poll_interval_sec}s ...")
        # Seed baseline state without triggering a run
        self._last_mtimes = self._current_mtimes()
        while True:
            time.sleep(poll_interval_sec)
            if self.has_new_files():
                logger.info("[FileWatcher] New files detected — triggering pipeline run.")
                try:
                    callback()
                except Exception as e:
                    logger.error(f"[FileWatcher] Pipeline run failed: {e}", exc_info=True)
