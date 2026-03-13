"""
obi_connector.py — Loads OBI (Oracle BI Publisher) feedback export → raw DataFrame.
Source: L-FDC US/CAN plants via OBI URL exports.
OBI exports may arrive as .csv or as HTML-disguised .xls files.
"""
import pandas as pd
from pathlib import Path
from .base_connector import BaseConnector


class OBIConnector(BaseConnector):
    source_name = "OBI (L-FDC)"

    def load(self) -> pd.DataFrame:
        suffix = self.file_path.suffix.lower()

        if suffix == ".csv":
            df = self._safe_read_csv(self.file_path, encoding="utf-8-sig")
        elif suffix in (".xls", ".xlsx"):
            try:
                # Many OBI .xls exports are actually HTML tables
                dfs = pd.read_html(str(self.file_path))
                df = dfs[0] if dfs else pd.DataFrame()
            except Exception:
                df = self._safe_read_excel(self.file_path)
        else:
            raise ValueError(f"[OBI] Unsupported file type: {suffix}")

        self._log_loaded(df)
        return df
