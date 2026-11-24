from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_GIS = ROOT / "data" / "processed" / "gis"

GEOJSON_NAMES = [
    "lake_water_extent.geojson",
    "historical_shorelines.geojson",
    "bathymetric_contours.geojson",
    "salt_crust_exposure.geojson",
    "urmia_basin_boundary.geojson",
    "subbasins.geojson",
]


def sync_all_geojson_copies() -> None:
    print("=== 1. Syncing updated GeoJSON files across all project directories ===")
    for name in GEOJSON_NAMES:
        src = SOURCE_GIS / name
        if not src.exists():
            print(f"[ERR] Source missing: {src}")
            continue
        matches = [
            p for p in ROOT.rglob(name)
            if "node_modules" not in p.parts and "dist" not in p.parts and p.resolve() != src.resolve()
        ]
        for dst in matches:
            shutil.copy2(src, dst)
            print(f"[SYNCED] {dst.relative_to(ROOT)}")


def patch_all_map_ts_files() -> None:
    print("\n=== 2. Searching & patching MapLibre layer expressions in web-dashboard/src ===")
    src_dir = ROOT / "web-dashboard" / "src"
    for path in src_dir.rglob("*"):
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        original = text

        if "historical" in text or "shoreline" in text or "year" in text:
            print(f"[FOUND LAYER REF] {path.relative_to(ROOT)}")

        # Ensure numeric matching for shoreline years (fixes fallback purple color)
        text = text.replace("['match', ['get', 'year'],", "['match', ['to-number', ['get', 'year'], 0],")
        text = text.replace('["match", ["get", "year"],', '["match", ["to-number", ["get", "year"], 0],')

        # Ensure numeric coercion for hazard & capacity expressions
        text = text.replace("['coalesce', ['get', 'dust_hazard_index'], 50]", "['to-number', ['get', 'dust_hazard_index'], 50]")
        text = text.replace("['coalesce', ['get', 'capacity_mcm'], 50]", "['to-number', ['get', 'capacity_mcm'], 50]")

        # Add cache-busting query param to GeoJSON fetches if fetched via URL
        if ".geojson" in text and "?v=2" not in text:
            text = text.replace(".geojson'", ".geojson?v=2'").replace('.geojson"', '.geojson?v=2"')
            text = text.replace(".geojson`", ".geojson?v=2`")

        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"[PATCHED] {path.relative_to(ROOT)}")


if __name__ == "__main__":
    sync_all_geojson_copies()
    patch_all_map_ts_files()
