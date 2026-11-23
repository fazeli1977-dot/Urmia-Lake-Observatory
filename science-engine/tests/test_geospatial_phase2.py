"""Phase 2 verification tests for spatial GeoJSON layers, CRS fidelity, and schema."""

import json
from pathlib import Path
import jsonschema
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
REF_DIR = ROOT / "data" / "reference" / "spatial"
WEB_GEO_DIR = ROOT / "web-dashboard" / "public" / "geo"
SCHEMA_PATH = ROOT / "schemas" / "spatial_manifest.schema.json"


def test_spatial_manifest_conforms_to_schema() -> None:
    manifest_path = REF_DIR / "spatial_manifest.json"
    assert manifest_path.exists(), "spatial_manifest.json must be generated first."
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=manifest, schema=schema)


def test_lake_boundary_valid_and_inside_watershed() -> None:
    lake_fc = json.loads((REF_DIR / "urmia_lake_boundary.geojson").read_text(encoding="utf-8"))
    basin_fc = json.loads((REF_DIR / "urmia_watershed_basin.geojson").read_text(encoding="utf-8"))

    lake_geom = shape(lake_fc["features"][0]["geometry"])
    basin_geom = shape(basin_fc["features"][0]["geometry"])

    assert lake_geom.is_valid, "Lake Urmia polygon must be topologically valid."
    assert basin_geom.is_valid, "Watershed polygon must be topologically valid."
    assert basin_geom.contains(lake_geom), "Watershed basin must strictly contain Lake Urmia."

    lake_area = lake_fc["features"][0]["properties"]["area_km2"]
    assert 4200 <= lake_area <= 6500, f"Unexpected Lake Urmia reference area: {lake_area} km2"


def test_major_rivers_and_web_sync() -> None:
    rivers_fc = json.loads((REF_DIR / "urmia_major_rivers.geojson").read_text(encoding="utf-8"))
    river_ids = {f["id"] for f in rivers_fc["features"]}
    assert "zarrineh_rud" in river_ids or "aji_chai" in river_ids
    assert len(rivers_fc["features"]) >= 5, "At least 5 major Urmia rivers must be extracted."

    for fname in [
        "urmia_lake_boundary.geojson",
        "urmia_watershed_basin.geojson",
        "urmia_subbasins.geojson",
        "urmia_major_rivers.geojson",
        "urmia_monitoring_landmarks.geojson",
        "spatial_manifest.json",
    ]:
        assert (WEB_GEO_DIR / fname).exists(), f"Missing synced web geo file: {fname}"