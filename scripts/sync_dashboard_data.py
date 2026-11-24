"""Synchronize verified scientific JSON outputs into web-dashboard/public/data."""
from pathlib import Path
import shutil
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA = ROOT / "web-dashboard" / "public" / "data"

SOURCES = {
    "lake_hydrology_latest.json": ROOT / "data" / "processed" / "lake_hydrology_latest.json",
    "lake_scientific_analytics_latest.json": ROOT / "data" / "processed" / "lake_scientific_analytics_latest.json",
    "era5_climate_latest.json": ROOT / "data" / "cache" / "era5_climate_latest.json",
}

def main() -> None:
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    synced = {}
    for target_name, src_path in SOURCES.items():
        if src_path.exists():
            shutil.copy2(src_path, PUBLIC_DATA / target_name)
            synced[target_name] = {
                "available": True,
                "size_bytes": src_path.stat().st_size,
                "source_relpath": str(src_path.relative_to(ROOT)).replace("\\", "/"),
            }
        else:
            synced[target_name] = {
                "available": False,
                "size_bytes": 0,
                "source_relpath": str(src_path.relative_to(ROOT)).replace("\\", "/"),
            }

    manifest = {
        "synced_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": synced,
    }
    (PUBLIC_DATA / "data_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[SYNC OK] Synced {sum(1 for v in synced.values() if v['available'])}/{len(SOURCES)} datasets to {PUBLIC_DATA}")

if __name__ == "__main__":
    main()