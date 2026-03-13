"""
validator.py — Data quality checks on the unified DataFrame.
Removes or flags rows that fail basic quality rules and logs a summary.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

MIN_VALID_YEAR = 2000


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply validation rules to the unified DataFrame.
    Returns a cleaned DataFrame. Logs counts of dropped/fixed rows.
    """
    original_len = len(df)

    # 1. Drop rows where incident_date is completely missing
    df = df[df["incident_date"].notna()].copy()
    after_date_drop = len(df)
    dropped_no_date = original_len - after_date_drop
    if dropped_no_date:
        logger.warning(f"[Validator] Dropped {dropped_no_date} rows with missing incident_date")

    # 2. Null-out dates before MIN_VALID_YEAR (epoch/placeholder artefacts)
    bad_year_mask = df["incident_date"].dt.year < MIN_VALID_YEAR
    n_bad_year = bad_year_mask.sum()
    if n_bad_year:
        df.loc[bad_year_mask, "incident_date"] = pd.NaT
        logger.warning(f"[Validator] Nulled {n_bad_year} dates before year {MIN_VALID_YEAR} "
                       f"(likely epoch/placeholder values)")

    # Drop rows that now have NaT because of the year guard
    df = df[df["incident_date"].notna()].copy()
    after_year_guard = len(df)
    dropped_year = after_date_drop - after_year_guard
    if dropped_year:
        logger.warning(f"[Validator] Dropped {dropped_year} rows after year guard ({MIN_VALID_YEAR})")

    # 3. Credit must be non-negative; clip negatives to 0 with a warning
    negative_credits = (df["credit_requested_usd"] < 0).sum()
    if negative_credits:
        logger.warning(f"[Validator] Clipped {negative_credits} negative credit values to 0")
        df["credit_requested_usd"] = df["credit_requested_usd"].clip(lower=0)

    # 4. Fill remaining NaN numerics with 0
    df["credit_requested_usd"] = df["credit_requested_usd"].fillna(0)
    df["qty_affected"]          = df["qty_affected"].fillna(0)

    # 5. Ensure string fields are clean strings
    for col in ["source", "plant", "customer", "defect_category"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()
        df[col] = df[col].replace({"nan": "Unknown", "": "Unknown"})

    logger.info(f"[Validator] Validation complete: {len(df)} / {original_len} rows retained")
    return df
