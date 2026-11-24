import json
import re
import requests
from shapely.geometry import LineString, Polygon, shape, mapping, MultiLineString
from shapely.ops import linemerge, unary_union
from pathlib import Path

ROOT = Path(".")
OUT_DIRS = [ROOT / "web-dashboard" / "public" / "geo", ROOT / "web-dashboard" / "dist" / "geo", ROOT / "public" / "geo"]
for d in OUT_DIRS: d.mkdir(parents=True, exist_ok=True)

# لیست فایل‌هایی که می‌دانیم باید آپدیت شوند (به جای خواندن از فایل خالی)
TARGET_FILES = ["urmia_major_rivers.geojson", "urmia_causeway.geojson", "urmia_wetlands.geojson"]

HEADERS = {"User-Agent": "UrmiaLakeScientific/2.0"}
OVERPASS_URL = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

def run_overpass(query: str):
    r = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=60)
    if r.status_code == 200: return r.json()
    raise RuntimeError(f"Overpass failed with code {r.status_code}")

def save_geojson(fc: dict, base_name: str):
    txt = json.dumps(fc, ensure_ascii=False)
    for d in OUT_DIRS:
        (d / base_name).write_text(txt, encoding="utf-8")
    print(f"Saved {base_name}")

# --- 1. میان‌گذر ---
print("Fetching Causeway...")
q_cw = '[out:json];way["highway"~"trunk|primary"](37.74,45.28,37.83,45.58);out geom;'
cw_data = run_overpass(q_cw)
lines = [LineString([(pt["lon"], pt["lat"]) for pt in el["geometry"]]) for el in cw_data.get("elements", []) if "geometry" in el]
if lines:
    save_geojson({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "Shahid Kalantari"}, "geometry": mapping(unary_union(lines))}]}, "urmia_causeway.geojson")

# --- 2. رودخانه‌ها (با هندسه امن) ---
print("Fetching Rivers...")
q_rv = '[out:json];way["waterway"="river"](36.3,44.8,38.3,47.0);out geom;'
rv_data = run_overpass(q_rv)
rivers = {}
for el in rv_data.get("elements", []):
    name = el.get("tags", {}).get("name:fa", "Unknown")
    if "geometry" in el:
        try:
            line = LineString([(pt["lon"], pt["lat"]) for pt in el["geometry"]])
            if line.is_valid:
                rivers.setdefault(name, []).append(line)
        except: continue

river_features = []
for name, segs in rivers.items():
    try:
        # استفاده از unary_union به تنهایی به جای linemerge برای جلوگیری از خطا
        merged = unary_union(segs)
        river_features.append({"type": "Feature", "properties": {"name": name}, "geometry": mapping(merged)})
    except: continue
save_geojson({"type": "FeatureCollection", "features": river_features}, "urmia_major_rivers.geojson")

# --- 3. تالاب‌ها ---
print("Fetching Wetlands...")
q_wl = '[out:json];way["natural"~"wetland|water"](36.85,45.0,38.10,46.05);out geom;'
wl_data = run_overpass(q_wl)
wl_features = []
for el in wl_data.get("elements", []):
    if "geometry" in el:
        try:
            poly = Polygon([(pt["lon"], pt["lat"]) for pt in el["geometry"]])
            if poly.is_valid and poly.area < 0.1:
                wl_features.append({"type": "Feature", "properties": {"name": el.get("tags", {}).get("name", "Wetland")}, "geometry": mapping(poly)})
        except: continue
save_geojson({"type": "FeatureCollection", "features": wl_features}, "urmia_wetlands.geojson")

print("Done! Cache version ?v=10_robust_real updated.")
