"""Phase 3 automated tests for UrmiaDataConnector and hypsometric physics."""
from __future__ import annotations

import json
from pathlib import Path

from src.data_connector import UrmiaDataConnector, interpolate_hypsometry


def test_hypsometry_monotonic_and_ecological_threshold():
    a_low, v_low = interpolate_hypsometry(1270.0)
    a_eco, v_eco = interpolate_hypsometry(1274.1)
    a_high, v_high = interpolate_hypsometry(1277.5)

    assert 500.0 <= a_low < a_eco < a_high
    assert 0.3 <= v_low < v_eco < v_high
    assert abs(a_eco - 4680.0) < 1.0


def test_processed_hydrology_artifact_exists_and_valid():
    root = Path(__file__).resolve().parents[2]
    artifact = root / "data" / "processed" / "lake_hydrology_latest.json"
    assert artifact.exists(), "Run scripts/run_phase3_sync.py before pytest"

    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["schema_version"] == "3.2.0"
    assert data["identifiers"]["cdse_clms_station_id"] == "1300000000142"
    assert len(data["water_level_timeseries"]) >= 15
    cur = data["current_status"]
    assert 1268.0 <= cur["water_level_m_asl"] <= 1280.0
    assert cur["estimated_area_km2"] > 0
    assert cur["estimated_volume_km3"] > 0