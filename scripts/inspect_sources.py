import json
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
print("=== 1. ALL SPATIAL / RAW FILES IN PROJECT ===")
exts = {".geojson", ".json", ".shp", ".gpkg", ".kml", ".kmz", ".tif", ".tiff"}
for p in sorted(ROOT.rglob("*")):
    if any(part in p.parts for part in ("node_modules", ".venv", ".git", "_backup_before_shoreline_clip")):
        continue
    if p.is_file() and p.suffix.lower() in exts:
        if p.suffix.lower() == ".json" and p.name in ("package.json", "package-lock.json", "tsconfig.json", "tsconfig.node.json"):
            continue
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size/1024:.1f} KB)")

print("\n=== 2. SCRIPTS THAT GENERATE GEOJSON ===")
for p in sorted((ROOT / "scripts").rglob("*.py")) if (ROOT / "scripts").exists() else []:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if "urmia_lake_boundary" in txt or "geojson" in txt.lower():
        print(f"  {p.relative_to(ROOT)}")
for p in sorted((ROOT / "src").rglob("*.py")) if (ROOT / "src").exists() else []:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if "urmia_lake_boundary" in txt or "geojson" in txt.lower():
        print(f"  {p.relative_to(ROOT)}")

print("\n=== 3. BOUNDARY GEOMETRY DETAILS ===")
bnd_path = ROOT / "web-dashboard" / "public" / "geo" / "urmia_lake_boundary.geojson"
gdf = gpd.read_file(bnd_path)
geom = gdf.geometry.iloc[0]
verts = sum(len(p.exterior.coords) for p in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]))
print(f"  Bounds (lon/lat): {[round(x, 4) for x in gdf.total_bounds]}")
print(f"  Vertex count: {verts}")
print(f"  Properties: {dict(gdf.iloc[0].drop(gdf.geometry.name))}")
