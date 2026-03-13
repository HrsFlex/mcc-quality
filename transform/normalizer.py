"""
normalizer.py — Maps each source's raw DataFrame to the unified schema.

Unified Schema
--------------
source               : str   — e.g. "Radius (L-MCC)"
plant                : str
customer             : str
incident_date        : datetime64[ns]
defect_category      : str
credit_requested_usd : float  (pre-conversion; actual USD conversion done in currency_converter)
qty_affected         : float
raw_source_file      : str   — original filename for audit
pipeline_run_id      : str   — UUID set by pipeline_runner
"""
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _coerce_numeric(val) -> float:
    return pd.to_numeric(val, errors="coerce")


# ─── Per-source mapping functions ─────────────────────────────────────────────

def _map_radius(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        if pd.isna(row.get("ReportDate")):
            continue
        rows.append({
            "source":               "Radius (L-MCC)",
            "plant":                str(row.get("Plant Name", "Unknown")).strip(),
            "customer":             str(row.get("Customer", "Unknown")).strip(),
            "incident_date":        row.get("ReportDate"),
            "defect_category":      str(row.get("Reason for Rejection", "Unknown")).strip(),
            "credit_requested_usd": _coerce_numeric(row.get("Value")),
            "qty_affected":         _coerce_numeric(row.get("Quantity")),
            "raw_source_file":      source_file,
        })
    return pd.DataFrame(rows)


def _map_fusion(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "source":               "Fusion (Rochester)",
            "plant":                "Rochester",
            "customer":             str(row.get("Customer", "Unknown")).strip(),
            "incident_date":        row.get("Create Date"),
            "defect_category":      str(row.get("Defect Type Sub Cat", "Unknown")).strip(),
            "credit_requested_usd": _coerce_numeric(row.get("Total Credit Requested")),
            "qty_affected":         _coerce_numeric(row.get("Total Labels Rejected")),
            "raw_source_file":      source_file,
        })
    return pd.DataFrame(rows)


def _map_vision(df: pd.DataFrame, source_file: str, plant_tag: str) -> pd.DataFrame:
    tag_map = {
        "OAK": ("Vision (Oak Creek)", "OAK CREEK PLANT"),
        "MAS": ("Vision (Mason)",     "MASON PLANT"),
    }
    source_label, default_plant = tag_map.get(plant_tag, (f"Vision ({plant_tag})", plant_tag))
    rows = []
    for _, row in df.iterrows():
        defect = (
            str(row.get("Type", "Unknown"))
            + " - "
            + str(row.get("Sub-Type", ""))
        ).strip(" -")
        rows.append({
            "source":               source_label,
            "plant":                str(row.get("Plant", default_plant)).strip(),
            "customer":             str(row.get("Customer Name", "Unknown")).strip(),
            "incident_date":        row.get("Report Date"),
            "defect_category":      defect,
            "credit_requested_usd": _coerce_numeric(row.get("Net Credit $")),
            "qty_affected":         _coerce_numeric(row.get("Defective Qty")),
            "raw_source_file":      source_file,
        })
    return pd.DataFrame(rows)


def _map_obi(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        date_val = row.get("Received Date", row.get("Received Dt"))
        defect = (
            str(row.get("General Category", ""))
            + " - "
            + str(row.get("Specific Category", ""))
        ).strip(" -")
        rows.append({
            "source":               "OBI (L-FDC)",
            "plant":                str(row.get("Plant Name", "Unknown")).strip(),
            "customer":             str(row.get("Customer", "Unknown")).strip(),
            "incident_date":        date_val,
            "defect_category":      defect,
            "credit_requested_usd": _coerce_numeric(row.get("Feedback Total Credit Requested")),
            "qty_affected":         _coerce_numeric(row.get("Qty in Question")),
            "raw_source_file":      source_file,
        })
    return pd.DataFrame(rows)


# ─── Public normalise function ─────────────────────────────────────────────────

def normalize(
    raw_frames: dict,
    run_id: str,
    fx_rates: Optional[dict] = None,
) -> pd.DataFrame:
    """
    raw_frames: dict keyed by source_key (from file_detector):
       "Radius"     → (DataFrame, file_path)
       "Fusion"     → (DataFrame, file_path)
       "Vision_OAK" → (DataFrame, file_path)
       "Vision_MAS" → (DataFrame, file_path)
       "OBI"        → (DataFrame, file_path)

    Returns a unified DataFrame with all sources stacked.
    """
    parts = []

    for key, (df, fpath) in raw_frames.items():
        fname = str(fpath)
        try:
            if key == "Radius":
                mapped = _map_radius(df, fname)
            elif key == "Fusion":
                mapped = _map_fusion(df, fname)
            elif key == "Vision_OAK":
                mapped = _map_vision(df, fname, "OAK")
            elif key == "Vision_MAS":
                mapped = _map_vision(df, fname, "MAS")
            elif key == "OBI":
                mapped = _map_obi(df, fname)
            else:
                logger.warning(f"[Normalizer] Unknown source key '{key}' — skipping")
                continue

            mapped["pipeline_run_id"] = run_id
            parts.append(mapped)
            logger.info(f"[Normalizer] {key}: {len(mapped)} rows mapped")
        except Exception as e:
            logger.error(f"[Normalizer] Failed to map {key}: {e}", exc_info=True)

    if not parts:
        logger.error("[Normalizer] No data to unify — all sources failed!")
        return pd.DataFrame()

    unified = pd.concat(parts, ignore_index=True)
    unified["incident_date"] = pd.to_datetime(unified["incident_date"], errors="coerce")

    # Apply FX conversion inline if rates provided
    if fx_rates:
        from transform.currency_converter import convert_to_usd
        unified = convert_to_usd(unified, fx_rates)

    logger.info(f"[Normalizer] Total unified rows: {len(unified)}")
    return unified
