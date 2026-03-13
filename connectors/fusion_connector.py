"""
fusion_connector.py — Loads Fusion (Rochester) Quality Data Excel → raw DataFrame.
Source: http://fusion.hammerpackaging.com  (Library Tools > Export to Excel)
"""
import pandas as pd
from .base_connector import BaseConnector


class FusionConnector(BaseConnector):
    source_name = "Fusion (Rochester)"

    def load(self) -> pd.DataFrame:
        df = self._safe_read_excel(self.file_path)
        self._log_loaded(df)
        return df
