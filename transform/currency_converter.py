"""
currency_converter.py — Converts credit amounts to USD based on plant name.
FX rates are sourced from config.py and can be overridden at runtime.
"""
import pandas as pd
from typing import Dict


def build_converter(fx_rates: Dict[str, float]):
    """
    Returns a vectorised conversion function that operates on a DataFrame.
    Plants NOT in fx_rates are assumed to already be in USD (multiplier = 1.0).
    """
    def convert_series(plants: pd.Series, amounts: pd.Series) -> pd.Series:
        multipliers = plants.map(lambda p: fx_rates.get(p, 1.0))
        return amounts * multipliers

    return convert_series


def convert_to_usd(df: pd.DataFrame, fx_rates: Dict[str, float]) -> pd.DataFrame:
    """
    In-place conversion of `credit_requested_usd` column using plant → FX rate map.
    Returns the mutated DataFrame.
    """
    converter = build_converter(fx_rates)
    df["credit_requested_usd"] = converter(df["plant"], df["credit_requested_usd"])
    return df
