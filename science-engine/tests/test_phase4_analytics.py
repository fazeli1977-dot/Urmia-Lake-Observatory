import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from src.analysis.trend_analysis import mann_kendall_test, sens_slope_per_year
from run_phase4_analytics import run_phase4_pipeline


def test_mann_kendall_monotonic_decreasing():
    vals = np.array([1278.0, 1276.5, 1275.0, 1273.2, 1271.8, 1270.4, 1269.8])
    res = mann_kendall_test(vals)
    assert res["significant"] is True
    assert res["trend"] == "decreasing"
    assert res["z_score"] < 0


def test_sens_slope_exact_annual_rate():
    dates = pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"]))
    vals = np.array([1272.0, 1271.5, 1271.0, 1270.5])
    res = sens_slope_per_year(dates, vals)
    assert abs(res["slope_per_year"] - (-0.5)) < 0.01


def test_phase4_full_pipeline_output():
    out = run_phase4_pipeline()
    out_file = Path("data/processed/lake_scientific_analytics_latest.json")
    assert out_file.exists()

    with out_file.open("r", encoding="utf-8") as f:
        saved = json.load(f)

    assert saved["schema_version"] == "4.0.0"
    assert "full_record" in saved["statistical_trends"]["periods"]
    hazard = saved["ecological_and_hazard_assessment"]["salt_dust_hazard"]
    assert 0.0 <= hazard["index_0_100"] <= 100.0
    assert hazard["hazard_tier"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}
