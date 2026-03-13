"""
test_connectors.py — Smoke tests for all source connectors.
Each test loads a real sample file and checks basic shape / column expectations.
"""
import os
import sys
import pytest
import pandas as pd

# Bootstrap path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg
from connectors.file_detector import detect_source_files


@pytest.fixture(scope="module")
def source_files():
    return detect_source_files(cfg.DATA_DIR, cfg.SOURCE_PATTERNS)


def test_radius_loads(source_files):
    path = source_files.get("Radius")
    if not path:
        pytest.skip("No Radius file found in DATA_DIR")
    from connectors.radius_connector import RadiusConnector
    df = RadiusConnector(path).load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "Report#" in df.columns or "Plant Name" in df.columns


def test_fusion_loads(source_files):
    path = source_files.get("Fusion")
    if not path:
        pytest.skip("No Fusion file found in DATA_DIR")
    from connectors.fusion_connector import FusionConnector
    df = FusionConnector(path).load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_vision_oak_loads(source_files):
    path = source_files.get("Vision_OAK")
    if not path:
        pytest.skip("No Vision OAK file found in DATA_DIR")
    from connectors.vision_connector import VisionConnector
    df = VisionConnector(path, plant_tag="OAK").load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_vision_mas_loads(source_files):
    path = source_files.get("Vision_MAS")
    if not path:
        pytest.skip("No Vision MAS file found in DATA_DIR")
    from connectors.vision_connector import VisionConnector
    df = VisionConnector(path, plant_tag="MAS").load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_obi_loads(source_files):
    path = source_files.get("OBI")
    if not path:
        pytest.skip("No OBI file found in DATA_DIR")
    from connectors.obi_connector import OBIConnector
    df = OBIConnector(path).load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
