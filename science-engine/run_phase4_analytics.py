import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analysis.trend_analysis import analyze_hydrology_trends
from src.analysis.ecological_risk import evaluate_ecological_and_dust_risk


def run_phase4_pipeline(
    input_path: str = "data/processed/lake_hydrology_latest.json",
    output_path: str = "data/processed/lake_scientific_analytics_latest.json",
) -> dict:
    in_file = Path(input_path)
    if not in_file.exists():
        raise FileNotFoundError(f"Phase 3 input file missing: {in_file}")

    with in_file.open("r", encoding="utf-8") as f:
        hydro_payload = json.load(f)

    trend_summary = analyze_hydrology_trends(str(in_file))
    eco_risk_summary = evaluate_ecological_and_dust_risk(hydro_payload)

    analytics_output = {
        "schema_version": "4.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_hydrology_schema": hydro_payload.get("schema_version", "unknown"),
        "upstream_generated_at": hydro_payload.get("generated_at", hydro_payload.get("generated_at_utc")),
        "station_metadata": hydro_payload.get("station_metadata", {"lake_name": "Urmia Lake"}),
        "statistical_trends": trend_summary,
        "ecological_and_hazard_assessment": eco_risk_summary,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(analytics_output, f, indent=2, ensure_ascii=False)

    return analytics_output


if __name__ == "__main__":
    result = run_phase4_pipeline()
    print("=== Phase 4 Scientific Analytics Generated Successfully ===")
    print(f"Output saved to: data/processed/lake_scientific_analytics_latest.json")
    eco = result["ecological_and_hazard_assessment"]
    print(json.dumps({
        "schema_version": result["schema_version"],
        "full_record_sens_slope_m_yr": result["statistical_trends"]["periods"]["full_record"]["sens_slope_m"]["slope_per_year"],
        "level_deficit_m": eco["ecological_benchmark"]["level_deficit_m"],
        "exposed_salt_playa_km2": eco["exposed_lakebed_playa"]["exposed_salt_playa_vs_ecological_km2"],
        "estimated_salinity_g_l": eco["salinity_and_biology"]["estimated_salinity_g_l"],
        "artemia_status": eco["salinity_and_biology"]["artemia_ecological_status"],
        "salt_dust_hazard_index": eco["salt_dust_hazard"]["index_0_100"],
        "salt_dust_hazard_tier": eco["salt_dust_hazard"]["hazard_tier"],
    }, indent=2, ensure_ascii=False))
