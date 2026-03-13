"""
vision_connector.py — Loads Vision NC Data Excel → raw DataFrame.
Handles both OAK CREEK (600) and MASON IR (006) by specifying plant_tag.
Source: Vision > Reports > Quality > Closed Non-Conformity Report (Excel)
"""
import pandas as pd
from .base_connector import BaseConnector

PLANT_LABELS = {
    "OAK": "Vision (Oak Creek)",
    "MAS": "Vision (Mason)",
}


class VisionConnector(BaseConnector):
    """
    plant_tag: "OAK" or "MAS" — controls which label is applied at normalisation.
    """

    def __init__(self, file_path: str, plant_tag: str = "OAK"):
        self.plant_tag = plant_tag.upper()
        self.source_name = PLANT_LABELS.get(self.plant_tag, f"Vision ({self.plant_tag})")
        super().__init__(file_path)

    def load(self) -> pd.DataFrame:
        df = self._safe_read_excel(self.file_path)
        # Tag the plant_tag so normalizer knows which label to apply
        df["_plant_tag"] = self.plant_tag
        self._log_loaded(df)
        return df
