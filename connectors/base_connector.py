"""
base_connector.py — Abstract base class for all source connectors.
All connectors must implement load() returning a raw pd.DataFrame.
"""
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class every source connector inherits from."""

    source_name: str = "Unknown"

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"[{self.source_name}] File not found: {self.file_path}")

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load raw data from the source file and return a DataFrame."""
        ...

    def _log_loaded(self, df: pd.DataFrame):
        logger.info(f"[{self.source_name}] Loaded {len(df)} rows from {self.file_path.name}")

    @staticmethod
    def _safe_read_excel(path: Path, **kwargs) -> pd.DataFrame:
        """Read Excel with a helpful error wrapper."""
        try:
            return pd.read_excel(path, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to read Excel file {path}: {e}") from e

    @staticmethod
    def _safe_read_csv(path: Path, **kwargs) -> pd.DataFrame:
        try:
            return pd.read_csv(path, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV file {path}: {e}") from e
