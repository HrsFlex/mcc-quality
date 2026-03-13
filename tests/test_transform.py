"""
test_transform.py — Unit tests for normalizer, validator, currency_converter.
Uses small synthetic DataFrames, no real files required.
"""
import sys, os
import pytest
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_raw_radius():
    return pd.DataFrame([{
        "Report#": "R001", "Plant Name": "MCC Louisville", "Customer": "Acme Corp",
        "ReportDate": "2025-06-15", "Reason for Rejection": "Color mismatch",
        "Value": "1500.00", "Quantity": "200",
    }])


def _make_raw_obi():
    return pd.DataFrame([{
        "Plant Name": "Niles Plant", "Customer": "Beta Inc",
        "Received Date": "2025-09-10", "General Category": "PRINT QUALITY ERRORS",
        "Specific Category": "COLOR", "Feedback Total Credit Requested": "3200",
        "Qty in Question": "500",
    }])


# ── Normalizer ─────────────────────────────────────────────────────────────────
def test_normalizer_unified_schema():
    from transform.normalizer import normalize
    raw_frames = {
        "Radius": (_make_raw_radius(), "fake_radius.xlsx"),
        "OBI":    (_make_raw_obi(),    "fake_obi.csv"),
    }
    result = normalize(raw_frames, run_id="test-run-001")
    expected_cols = ["source", "plant", "customer", "incident_date",
                     "defect_category", "credit_requested_usd", "qty_affected",
                     "pipeline_run_id"]
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
    assert len(result) == 2


def test_normalizer_run_id_stamped():
    from transform.normalizer import normalize
    raw_frames = {"Radius": (_make_raw_radius(), "fake_radius.xlsx")}
    result = normalize(raw_frames, run_id="my-run-123")
    assert (result["pipeline_run_id"] == "my-run-123").all()


# ── Validator ──────────────────────────────────────────────────────────────────
def test_validator_removes_ancient_dates():
    from transform.validator import validate
    df = pd.DataFrame([
        {"source": "Test", "plant": "PL", "customer": "C",
         "incident_date": pd.Timestamp("1900-01-01"),
         "defect_category": "X", "credit_requested_usd": 100, "qty_affected": 10},
        {"source": "Test", "plant": "PL", "customer": "C",
         "incident_date": pd.Timestamp("2025-06-01"),
         "defect_category": "X", "credit_requested_usd": 200, "qty_affected": 5},
    ])
    clean = validate(df)
    assert len(clean) == 1
    assert clean.iloc[0]["credit_requested_usd"] == 200


def test_validator_clips_negative_credits():
    from transform.validator import validate
    df = pd.DataFrame([{
        "source": "Test", "plant": "PL", "customer": "C",
        "incident_date": pd.Timestamp("2025-03-01"),
        "defect_category": "Y", "credit_requested_usd": -500, "qty_affected": 0,
    }])
    clean = validate(df)
    assert clean.iloc[0]["credit_requested_usd"] == 0


def test_validator_fills_null_strings():
    from transform.validator import validate
    df = pd.DataFrame([{
        "source": None, "plant": None, "customer": None,
        "incident_date": pd.Timestamp("2025-01-01"),
        "defect_category": None, "credit_requested_usd": 0, "qty_affected": 0,
    }])
    clean = validate(df)
    assert clean.iloc[0]["source"] == "Unknown"


# ── Currency Converter ─────────────────────────────────────────────────────────
def test_currency_converter_mxn():
    from transform.currency_converter import convert_to_usd
    df = pd.DataFrame([
        {"plant": "MCC Monterrey", "credit_requested_usd": 1000},
        {"plant": "Rochester",     "credit_requested_usd": 500},
    ])
    result = convert_to_usd(df, {"MCC Monterrey": 0.05})
    assert result.loc[0, "credit_requested_usd"] == pytest.approx(50.0)
    assert result.loc[1, "credit_requested_usd"] == pytest.approx(500.0)
