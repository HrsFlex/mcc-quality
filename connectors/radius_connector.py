"""
radius_connector.py — Loads Radius MDA Report Excel → raw DataFrame.
Source: L-MCC Plants  (Radius > MCC Custom Reports > Quality > MDA > MDA Log Multi-Plant)
"""
import pandas as pd
from .base_connector import BaseConnector


class RadiusConnector(BaseConnector):
    source_name = "Radius (L-MCC)"

    def load(self) -> pd.DataFrame:
        df = self._safe_read_excel(self.file_path)
        # Keep only rows that have a Report# (header/footer noise rows won't have one)
        if "Report#" in df.columns:
            df = df.dropna(subset=["Report#"])
        self._log_loaded(df)
        return df
