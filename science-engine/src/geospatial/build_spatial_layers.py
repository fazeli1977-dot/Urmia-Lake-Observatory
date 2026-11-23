"""Phase 2 CLI pipeline: build, validate, and publish ULO spatial GeoJSON layers."""

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Dict, Any
import jsonschema

from src.config.urmia_config import GEOGRAPHIC_CRS_EPSG, METRIC_CRS_EPSG
from src.geospatial.osm_ingestor import (
    fetch_urmia_lake_boundary,
    fetch_urmia_major_rivers,
)
from src.geospatial.reference_features import (
    build_landmarks_geojson,
    build_subbasins_geojson,
    build_watershed_geojson,
)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_spatial_pipeline() -> Dict[str, Any]:
    root = get_project_root()
    raw_dir = root / "data" / "raw" / "geospatial"
    ref_dir = root / "data" / "reference" / "spatial"
    web_geo_dir = root / "web-dashboard" / "public" / "geo"
    schema_path = root / "schemas" / "spatial_manifest.schema.json"

    print("[Phase 2] Fetching real Lake Urmia boundary...")
    lake_fc = fetch_urmia_lake_boundary(raw_dir)

    print("[Phase 2] Building watershed & hydrological sub-basins...")
    watershed_fc = build_watershed_geojson()
    subbasins_fc = build_subbasins_geojson()

    print("[Phase 2] Fetching canonical Urmia Basin rivers from OpenStreetMap...")
    rivers_fc = fetch_urmia_major_rivers(raw_dir)

    print("[Phase 2] Building scientific & hydraulic monitoring landmarks...")
    landmarks_fc = build_landmarks_geojson()

    layer_files = {
        "lake_boundary": ("urmia_lake_boundary.geojson", lake_fc),
        "watershed_basin": ("urmia_watershed_basin.geojson", watershed_fc),
        "subbasins": ("urmia_subbasins.geojson", subbasins_fc),
        "major_rivers": ("urmia_major_rivers.geojson", rivers_fc),
        "monitoring_landmarks": ("urmia_monitoring_landmarks.geojson", landmarks_fc),
    }

    web_geo_dir.mkdir(parents=True, exist_ok=True)
    layers_manifest_meta: Dict[str, Any] = {}

    for key, (filename, fc_data) in layer_files.items():
        ref_target = ref_dir / filename
        web_target = web_geo_dir / filename
        _write_json(ref_target, fc_data)
        shutil.copyfile(ref_target, web_target)
        layers_manifest_meta[key] = {
            "file": f"/geo/{filename}",
            "feature_count": len(fc_data["features"]),
        }

    lake_area = lake_fc["features"][0]["properties"]["area_km2"]
    watershed_area = watershed_fc["features"][0]["properties"]["area_km2"]
    rivers_count = len(rivers_fc["features"])
    rivers_total_km = round(
        sum(f["properties"]["mapped_length_km"] for f in rivers_fc["features"]), 2
    )
    landmarks_count = len(landmarks_fc["features"])

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "geographic_crs": GEOGRAPHIC_CRS_EPSG,
        "metric_crs": METRIC_CRS_EPSG,
        "summary_metrics": {
            "lake_reference_bed_area_km2": lake_area,
            "watershed_area_km2": watershed_area,
            "mapped_rivers_count": rivers_count,
            "mapped_rivers_total_length_km": rivers_total_km,
            "monitoring_landmarks_count": landmarks_count,
        },
        "layers": layers_manifest_meta,
    }

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=manifest, schema=schema)

    _write_json(ref_dir / "spatial_manifest.json", manifest)
    _write_json(web_geo_dir / "spatial_manifest.json", manifest)

    print(
        f"[Phase 2] Spatial layers verified -> "
        f"Lake Bed: {lake_area} km2 | Basin: {watershed_area} km2 | "
        f"Rivers: {rivers_count} ({rivers_total_km} km) | Landmarks: {landmarks_count}"
    )
    return manifest


if __name__ == "__main__":
    run_spatial_pipeline()