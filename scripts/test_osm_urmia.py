import json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

print("=== 1. INSPECT lake_urmia_raw_source.json COORDS ===")
raw = json.loads((ROOT / "data/raw/geospatial/lake_urmia_raw_source.json").read_text(encoding="utf-8"))
ring = raw["coordinates"][0]
lats = [p[1] for p in ring]
lons = [p[0] for p in ring]
print(f"Total pts: {len(ring)}, Lon: {min(lons):.4f}..{max(lons):.4f}, Lat: {min(lats):.4f}..{max(lats):.4f}")
north_pts = sorted(ring, key=lambda p: -p[1])[:10]
print("Top 10 northernmost pts in raw_source:", [(round(x,4), round(y,4)) for x,y in north_pts])

print("\n=== 2. TEST OVERPASS / NOMINATIM REAL OSM FETCH FOR LAKE URMIA ===")
try:
    url = "https://nominatim.openstreetmap.org/search?q=Lake+Urmia&format=json&polygon_geojson=1&limit=5"
    req = urllib.request.Request(url, headers={"User-Agent": "UrmiaLakeObservatory/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for i, item in enumerate(data):
        gj = item.get("geojson", {})
        t = gj.get("type")
        bb = item.get("boundingbox")
        ot = item.get("osm_type")
        oid = item.get("osm_id")
        cl = item.get("class")
        tp = item.get("type")
        nm = item.get("display_name", "")[:60]
        coords = gj.get("coordinates", [])
        npts = len(coords[0]) if t == "Polygon" and coords else (sum(len(p[0]) for p in coords) if t == "MultiPolygon" and coords else 0)
        print(f"  [{i}] osm={ot}/{oid} {cl}/{tp} geom={t} pts={npts} bbox={bb} name={nm}")
except Exception as e:
    print("  Nominatim fetch error:", e)

print("\n=== 3. REST OF rebuild_public_geo_layers.py (lines 90..end) ===")
rp = (ROOT / "scripts/rebuild_public_geo_layers.py").read_text(encoding="utf-8").splitlines()
print(f"Total lines: {len(rp)}")
print("\n".join(rp[90:240]))
