import json
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

print("=== A. RAW SOURCE: lake_urmia_raw_source.json ===")
raw_p = ROOT / "data" / "raw" / "geospatial" / "lake_urmia_raw_source.json"
if raw_p.exists():
    txt = raw_p.read_text(encoding="utf-8")
    obj = json.loads(txt)
    print("  Keys:", list(obj.keys()) if isinstance(obj, dict) else type(obj))
    try:
        gdf = gpd.read_file(raw_p)
        print("  GeoDataFrame rows:", len(gdf), "bounds:", [round(x, 4) for x in gdf.total_bounds])
        for i, r in gdf.iterrows():
            g = r.geometry
            v = sum(len(p.exterior.coords) for p in (g.geoms if g.geom_type == "MultiPolygon" else [g])) if g.geom_type in ("Polygon","MultiPolygon") else len(g.coords) if g.geom_type=="LineString" else -1
            props = {k: r[k] for k in r.index if k != "geometry"}
            print(f"    [{i}] {g.geom_type} verts={v} bounds={[round(x,4) for x in g.bounds]} props={props}")
    except Exception as e:
        print("  Not direct GeoJSON:", e, "Preview:", txt[:400])

print("\n=== B. PROCESSED GIS FILES (data/processed/gis) ===")
for p in sorted((ROOT / "data" / "processed" / "gis").glob("*.geojson")):
    gdf = gpd.read_file(p)
    print(f"  {p.name}: rows={len(gdf)}, geom={list(gdf.geom_type.unique())}, bounds={[round(x,4) for x in gdf.total_bounds]}")
    cols = [c for c in gdf.columns if c != "geometry"]
    print(f"    cols={cols}")
    for i, r in gdf.head(6).iterrows():
        d = {c: r[c] for c in cols}
        print(f"    row[{i}]: bounds={[round(x,4) for x in r.geometry.bounds]} props={d}")

print("\n=== C. PUBLIC/GEO SCHEMA (expected properties by frontend) ===")
for name in ["urmia_lake_boundary.geojson", "urmia_active_water.geojson", "urmia_desiccated_zones.geojson", "urmia_hypsometric_contours.geojson", "urmia_shorelines.geojson"]:
    p = ROOT / "web-dashboard" / "public" / "geo" / name
    gdf = gpd.read_file(p)
    cols = [c for c in gdf.columns if c != "geometry"]
    print(f"  {name}: rows={len(gdf)} cols={cols}")
    for i, r in gdf.iterrows():
        print(f"    [{i}]", {c: r[c] for c in cols})

print("\n=== D. HEAD OF rebuild_public_geo_layers.py ===")
rp = ROOT / "scripts" / "rebuild_public_geo_layers.py"
if rp.exists():
    print("\n".join(rp.read_text(encoding="utf-8").splitlines()[:90]))
