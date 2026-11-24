"""Execute Phase 3.2 Hydrology & Climate Sync and print diagnostic summary."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "science-engine"))

from src.data_connector import UrmiaDataConnector


def main() -> int:
    print("== Phase 3.2: Running Urmia Lake Hydrology, STAC Altimetry & ERA5 Sync ==")
    connector = UrmiaDataConnector(project_root=ROOT)
    payload = connector.sync_all()

    prov = payload["data_provenance"]
    cur = payload["current_status"]
    stac = payload["stac_live_catalog"]

    print(f"   [OK] Output saved -> data/processed/lake_hydrology_latest.json")
    print(f"   Provenance Mode       : {prov['water_level_mode']}")
    print(f"   Live STAC Metadata    : {prov['stac_metadata_live']}")
    print(f"     - CDSE Latest Prod  : {stac.get('cdse_clms_wl', {}).get('latest_product_id')}")
    print(f"     - Hydroweb End Date : {stac.get('hydroweb_ope', {}).get('end_datetime')}")
    print(f"   Live ERA5 Climate     : {prov['climate_era5_live']} "
          f"(months={len(payload['basin_climate_era5']['monthly_summary'])})")
    print("   --- Current Lake Urmia Hydrological Indicators ---")
    print(f"   Reference Date        : {cur['observation_date']}")
    print(f"   Water Level (m a.s.l.): {cur['water_level_m_asl']} m "
          f"(Ecological deficit: -{cur['ecological_deficit_m']} m vs {cur['ecological_target_m_asl']} m)")
    print(f"   Surface Area (est.)   : {cur['estimated_area_km2']} km2")
    print(f"   Water Volume (est.)   : {cur['estimated_volume_km3']} km3 "
          f"(Deficit: -{cur['ecological_volume_deficit_km3']} km3)")
    print(f"   Trailing 12m Precip   : {cur['trailing_12m_precip_mm']} mm | ET0: {cur['trailing_12m_et0_mm']} mm")
    print(f"   Timeseries Points     : {len(payload['water_level_timeseries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())