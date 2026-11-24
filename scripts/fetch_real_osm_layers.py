#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch REAL OpenStreetMap geometry WITHOUT Overpass (blocked on this network).
Sources:
  1. OSM Core API v0.6 /api/0.6/map.json  -> causeway (highway ways)
  2. Nominatim Search API format=geojson  -> rivers & wetlands (polygon_geojson=1)

CRITICAL RULE: Never overwrite an existing file with features: [].
If a source returns zero features, the previous file is left untouched.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Ensure UTF-8 stdout on Windows (avoid cp1252 encode errors with Persian labels)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
GEO_DIR = ROOT / "web-dashboard" / "public" / "geo"
REFERENCE_DIR = ROOT / "data" / "reference" / "spatial"
GEO_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "UrmiaLakeObservatory/1.0 (real-osm-fetch; contact: alirezafazeli@live.com)",
    "Accept": "application/json",
}

REQUEST_TIMEOUT = 45
NOMINATIM_DELAY = 1.2  # seconds between Nominatim requests (usage policy)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_existing(name: str) -> Optional[Dict[str, Any]]:
    p = GEO_DIR / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_if_nonempty(name: str, geojson: Dict[str, Any]) -> int:
    """Write only if geojson has features. Returns number of features written."""
    n = len(geojson.get("features", []))
    if n == 0:
        existing = load_existing(name)
        existing_n = len(existing.get("features", [])) if existing else 0
        print(f"  [SKIP] {name}: new data empty, keeping existing ({existing_n} features)")
        return existing_n
    out_path = GEO_DIR / name
    out_path.write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  [WROTE] {name} ({n} features)")
    return n


def osm_element_to_feature(el: Dict[str, Any], layer_name: str, fid: int) -> Optional[Dict[str, Any]]:
    """Convert an OSM element (from Nominatim) to a GeoJSON Feature."""
    etype = el.get("type")
    tags = el.get("tags", {}) or {}

    if etype == "way":
        nodes = el.get("nodes", [])
        coords: List[Tuple[float, float]] = []
        for nid in nodes:
            lat = nid.get("lat") if isinstance(nid, dict) else None
            lon = nid.get("lon") if isinstance(nid, dict) else None
            if lat is not None and lon is not None:
                coords.append((float(lon), float(lat)))
        if len(coords) < 2:
            return None
        if len(coords) >= 4 and coords[0] == coords[-1]:
            geom: Dict[str, Any] = {"type": "Polygon", "coordinates": [coords]}
        else:
            geom = {"type": "LineString", "coordinates": coords}
    elif etype == "relation":
        return None
    else:
        return None

    props = {"id": f"{layer_name}_{etype}{el.get('id','')}", "osm_id": el.get("id"), "osm_type": etype}
    for k, v in tags.items():
        props[k] = v
    return {"type": "Feature", "properties": props, "geometry": geom}


# ---------------------------------------------------------------------------
# 1. Causeway via OSM Core API v0.6
# ---------------------------------------------------------------------------
def fetch_causeway() -> int:
    print("\n[FETCH] urmia_causeway.geojson  (OSM Core API v0.6 map.json)")
    bbox = "45.20,37.70,45.60,37.85"
    url = f"https://api.openstreetmap.org/api/0.6/map.json?bbox={bbox}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            print(f"  [WARN] OSM Core API HTTP {r.status_code}")
            existing = load_existing("urmia_causeway.geojson")
            return len(existing.get("features", [])) if existing else 0
        data = r.json()
    except Exception as exc:
        print(f"  [WARN] OSM Core API error: {exc}")
        existing = load_existing("urmia_causeway.geojson")
        return len(existing.get("features", [])) if existing else 0

    elements = data.get("elements", [])
    print(f"  elements={len(elements)}")

    # Build node lookup: id -> (lon, lat)
    node_coords: Dict[int, Tuple[float, float]] = {}
    for el in elements:
        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is not None and lon is not None:
                node_coords[el["id"]] = (float(lon), float(lat))

    highway_tags = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link"}
    features: List[Dict[str, Any]] = []
    fid = 1
    for el in elements:
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {}) or {}
        hw = tags.get("highway", "")
        if hw not in highway_tags:
            continue
        node_ids = el.get("nodes", [])
        coords = [node_coords[nid] for nid in node_ids if nid in node_coords]
        if len(coords) < 2:
            continue
        if len(coords) >= 4 and coords[0] == coords[-1]:
            geom: Dict[str, Any] = {"type": "Polygon", "coordinates": [coords]}
        else:
            geom = {"type": "LineString", "coordinates": coords}

        props = {
            "id": f"causeway_w{el['id']}",
            "osm_id": el.get("id"),
            "osm_type": "way",
            "highway": hw,
        }
        for k, v in tags.items():
            if k not in props:
                props[k] = v
        features.append({"type": "Feature", "properties": props, "geometry": geom})
        fid += 1

    geojson = {"type": "FeatureCollection", "name": "urmia_causeway", "features": features}
    return write_if_nonempty("urmia_causeway.geojson", geojson)


# ---------------------------------------------------------------------------
# 2. Rivers via Nominatim GeoJSON API
# ---------------------------------------------------------------------------
RIVERS = [
    "زرینه رود", "سیمینه رود", "آجی چای", "تلخه رود", "گدارچای",
    "مهابادچای", "باراندوزچای", "شهرچای", "نازلوچای", "زولاچای",
    "صوفی چای", "قلعه چای",
]


def fetch_rivers() -> int:
    print("\n[FETCH] urmia_major_rivers.geojson  (Nominatim GeoJSON API)")
    seen_ids = set()
    features: List[Dict[str, Any]] = []
    fid = 1

    for name in RIVERS:
        time.sleep(NOMINATIM_DELAY)
        params = {
            "format": "geojson",
            "polygon_geojson": 1,
            "viewbox": "44.5,38.6,47.5,36.0",
            "bounded": 1,
            "limit": 5,
            "q": name,
        }
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                print(f"  [WARN] Nominatim '{name}' HTTP {r.status_code}")
                continue
            fc = r.json()
        except Exception as exc:
            print(f"  [WARN] Nominatim '{name}' error: {exc}")
            continue

        for feat in fc.get("features", []):
            geom = feat.get("geometry", {})
            gtype = geom.get("type", "")
            if gtype not in ("LineString", "MultiLineString"):
                continue
            props = feat.get("properties", {})
            osm_id = props.get("osm_id")
            osm_type = props.get("osm_type", "")
            uid = f"{osm_type}{osm_id}"
            if uid in seen_ids:
                continue
            seen_ids.add(uid)
            new_props = {
                "id": f"river_{fid}",
                "osm_id": osm_id,
                "osm_type": osm_type,
                "name": props.get("display_name", name),
                "river_name_fa": name,
            }
            for k in ("category", "type", "importance"):
                if k in props:
                    new_props[k] = props[k]
            features.append({"type": "Feature", "properties": new_props, "geometry": geom})
            fid += 1

        print(f"  '{name}' -> {len(fc.get('features', []))} results")

    geojson = {"type": "FeatureCollection", "name": "urmia_major_rivers", "features": features}
    return write_if_nonempty("urmia_major_rivers.geojson", geojson)


# ---------------------------------------------------------------------------
# 3. Wetlands via Nominatim GeoJSON API
# ---------------------------------------------------------------------------
WETLANDS = [
    "تالاب کانی برازان", "تالاب قوری گل", "تالاب شورگل", "تالاب یادگارلو",
    "تالاب درگه سنگی", "تالاب حسنلو", "تالاب قره قشلاق",
]


def fetch_wetlands() -> int:
    print("\n[FETCH] urmia_riparian_vegetation.geojson  (Nominatim GeoJSON API)")
    seen_ids = set()
    features: List[Dict[str, Any]] = []
    fid = 1

    for name in WETLANDS:
        time.sleep(NOMINATIM_DELAY)
        params = {
            "format": "geojson",
            "polygon_geojson": 1,
            "viewbox": "44.5,38.6,47.5,36.0",
            "bounded": 1,
            "limit": 5,
            "q": name,
        }
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                print(f"  [WARN] Nominatim '{name}' HTTP {r.status_code}")
                continue
            fc = r.json()
        except Exception as exc:
            print(f"  [WARN] Nominatim '{name}' error: {exc}")
            continue

        for feat in fc.get("features", []):
            geom = feat.get("geometry", {})
            gtype = geom.get("type", "")
            if gtype not in ("Polygon", "MultiPolygon"):
                continue
            props = feat.get("properties", {})
            osm_id = props.get("osm_id")
            osm_type = props.get("osm_type", "")
            uid = f"{osm_type}{osm_id}"
            if uid in seen_ids:
                continue
            seen_ids.add(uid)
            new_props = {
                "id": f"wetland_{fid}",
                "osm_id": osm_id,
                "osm_type": osm_type,
                "name": props.get("display_name", name),
                "eco_type": "satellite_freshwater_brackish_wetland",
            }
            features.append({"type": "Feature", "properties": new_props, "geometry": geom})
            fid += 1

        print(f"  '{name}' -> {len(fc.get('features', []))} results")

    geojson = {"type": "FeatureCollection", "name": "urmia_riparian_vegetation", "features": features}
    return write_if_nonempty("urmia_riparian_vegetation.geojson", geojson)


# ---------------------------------------------------------------------------
# Fallback: restore from reference/spatial if Nominatim returned nothing
# ---------------------------------------------------------------------------
def restore_from_reference(name: str) -> int:
    src = REFERENCE_DIR / name
    if not src.exists():
        print(f"  [WARN] No reference backup for {name}")
        return 0
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
        n = len(data.get("features", []))
        if n > 0:
            out_path = GEO_DIR / name
            out_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  [RESTORED] {name} from reference/spatial ({n} features)")
            return n
    except Exception as exc:
        print(f"  [WARN] Could not read reference backup {name}: {exc}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== REAL OSM FETCH (No Overpass) ===")
    n_causeway = fetch_causeway()
    n_rivers = fetch_rivers()
    n_wetlands = fetch_wetlands()

    # Fallbacks
    if n_wetlands == 0:
        print("  [FALLBACK] Restoring wetlands from reference/spatial backup")
        n_wetlands = restore_from_reference("urmia_riparian_vegetation.geojson")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
