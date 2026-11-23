"""Real geospatial boundary & river extractor using OpenStreetMap Overpass & Natural Earth."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from shapely.geometry import LineString, MultiLineString, Polygon, shape, mapping
from shapely.ops import linemerge, polygonize, unary_union

from src.geospatial.crs_utils import (
    compute_area_perimeter_km,
    compute_length_km,
    ensure_valid_geometry,
)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

NATURAL_EARTH_LAKES_10M_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_10m_lakes.geojson"
)

HEADERS = {
    "User-Agent": "UrmiaLakeObservatory/0.2 (+mailto:alirezafazeli@live.com; scientific-research)"
}

# Canonical rivers of Lake Urmia Basin with Persian/English names & matching keywords
CANONICAL_RIVERS = [
    {
        "id": "zarrineh_rud",
        "name_fa": "زرینه‌رود (جغتو)",
        "name_en": "Zarrineh Rud",
        "subbasin": "subbasin_south",
        "keywords": ["زرینه", "Zarrineh", "Zarineh", "Jaghata", "جغتو"],
    },
    {
        "id": "simineh_rud",
        "name_fa": "سیمینه‌رود (تاتائو)",
        "name_en": "Simineh Rud",
        "subbasin": "subbasin_south",
        "keywords": ["سیمینه", "Simineh", "تاتائو"],
    },
    {
        "id": "aji_chai",
        "name_fa": "آجی‌چای (تلخه‌رود)",
        "name_en": "Aji Chai (Talkheh Rud)",
        "subbasin": "subbasin_east",
        "keywords": ["آجی", "تلخه", "Aji", "Talkheh", "Acı"],
    },
    {
        "id": "gadar_chai",
        "name_fa": "گدارچای",
        "name_en": "Gadar Chai",
        "subbasin": "subbasin_west",
        "keywords": ["گدار", "Gadar", "Qadar"],
    },
    {
        "id": "mahabad_chai",
        "name_fa": "مهابادچای",
        "name_en": "Mahabad Chai",
        "subbasin": "subbasin_south",
        "keywords": ["مهاباد", "Mahabad"],
    },
    {
        "id": "baranduz_chai",
        "name_fa": "باراندوزچای",
        "name_en": "Baranduz Chai",
        "subbasin": "subbasin_west",
        "keywords": ["باراندوز", "Baranduz", "Barandooz"],
    },
    {
        "id": "shahr_chai",
        "name_fa": "شهرچای (ارومیه)",
        "name_en": "Shahr Chai",
        "subbasin": "subbasin_west",
        "keywords": ["شهرچای", "شهر چای", "Shahr Chai", "Shahrchay"],
    },
    {
        "id": "nazlu_chai",
        "name_fa": "نازلوچای",
        "name_en": "Nazlu Chai",
        "subbasin": "subbasin_west",
        "keywords": ["نازلو", "Nazlu", "Nazloo"],
    },
    {
        "id": "zola_chai",
        "name_fa": "زولاچای (سلماس)",
        "name_en": "Zola Chai",
        "subbasin": "subbasin_north",
        "keywords": ["زولا", "Zola"],
    },
    {
        "id": "sufi_chai",
        "name_fa": "صوفی‌چای (مراغه)",
        "name_en": "Sufi Chai",
        "subbasin": "subbasin_east",
        "keywords": ["صوفی", "Sufi", "Soufi"],
    },
]


def _query_overpass(query: str, timeout_sec: int = 55) -> Optional[Dict[str, Any]]:
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(
                endpoint,
                data={"data": query},
                headers=HEADERS,
                timeout=timeout_sec,
            )
            if resp.status_code == 200:
                payload = resp.json()
                if payload.get("elements"):
                    return payload
        except Exception:
            continue
    return None


def fetch_urmia_lake_boundary(raw_cache_dir: Path) -> Dict[str, Any]:
    """Fetch real Lake Urmia boundary from Natural Earth 10m or OSM Overpass."""
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = raw_cache_dir / "lake_urmia_raw_source.json"

    lake_geom = None
    source_name = ""

    # Strategy 1: Natural Earth 10m Lakes (clean, topologically closed global cartographic standard)
    try:
        resp = requests.get(NATURAL_EARTH_LAKES_10M_URL, headers=HEADERS, timeout=45)
        if resp.status_code == 200:
            ne_data = resp.json()
            matched_polys = []
            for feat in ne_data.get("features", []):
                props = feat.get("properties") or {}
                names_blob = " ".join(
                    str(props.get(k, "")) for k in ("name", "name_en", "name_alt", "name_fa")
                ).lower()
                if "urmia" in names_blob or "orumiyeh" in names_blob or "ارومیه" in names_blob:
                    matched_polys.append(shape(feat["geometry"]))
            if matched_polys:
                lake_geom = ensure_valid_geometry(unary_union(matched_polys))
                source_name = "Natural Earth 10m Lakes (ne_10m_lakes.geojson)"
                cache_file.write_text(
                    json.dumps(mapping(lake_geom), ensure_ascii=False), encoding="utf-8"
                )
    except Exception:
        pass

    # Strategy 2: OpenStreetMap Overpass API outer relation of Lake Urmia
    if lake_geom is None:
        overpass_lake_q = """
        [out:json][timeout:45];
        (
          relation["natural"="water"]["name:en"~"Urmia",i](36.9,44.9,38.4,46.1);
          relation["natural"="water"]["name"~"ارومیه"](36.9,44.9,38.4,46.1);
        );
        out geom;
        """
        osm_data = _query_overpass(overpass_lake_q)
        if osm_data:
            outer_lines = []
            for el in osm_data.get("elements", []):
                for member in el.get("members", []):
                    if member.get("role") in ("outer", "") and member.get("geometry"):
                        coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
                        if len(coords) >= 2:
                            outer_lines.append(LineString(coords))
            polys = list(polygonize(unary_union(outer_lines)))
            if polys:
                # Filter polygons larger than 500 km2
                big_polys = [p for p in polys if compute_area_perimeter_km(p)[0] > 500]
                if big_polys:
                    lake_geom = ensure_valid_geometry(unary_union(big_polys))
                    source_name = "OpenStreetMap Overpass API (Lake Urmia Water Relation)"

    # Strategy 3: Cached raw geometry if offline
    if lake_geom is None and cache_file.exists():
        cached_geojson = json.loads(cache_file.read_text(encoding="utf-8"))
        lake_geom = ensure_valid_geometry(shape(cached_geojson))
        source_name = "Cached Natural Earth / OSM Geometry"

    if lake_geom is None:
        raise RuntimeError(
            "Unable to fetch real Lake Urmia boundary from Natural Earth or OpenStreetMap. "
            "Check internet connectivity; mock fallback is strictly prohibited."
        )

    # Simplify slightly (~90m tolerance = 0.0008 deg) for crisp web rendering while preserving metric fidelity
    web_geom = ensure_valid_geometry(lake_geom.simplify(0.0008, preserve_topology=True))
    area_km2, perimeter_km = compute_area_perimeter_km(web_geom)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "lake_urmia_historical_bed",
                "properties": {
                    "id": "lake_urmia_historical_bed",
                    "name_fa": "پهنه مرجع بستر دریاچه ارومیه",
                    "name_en": "Lake Urmia Reference Lakebed Envelope",
                    "area_km2": area_km2,
                    "perimeter_km": perimeter_km,
                    "ecological_target_level_masl": 1274.1,
                    "crs": "EPSG:4326",
                    "metric_crs_used": "EPSG:32638",
                    "source_lineage": source_name,
                    "scientific_note_fa": "این پلیگون مرز مرجع کارتای بستر دریاچه است؛ مساحت واقعی آب در هر تاریخ در فاز ۳ و ۴ از تصاویر ماهواره‌ای استخراج می‌شود.",
                    "scientific_note_en": "Reference cartographic lakebed boundary; dynamic open-water vs. salt-crust area is derived from satellite imagery in Phases 3-4.",
                },
                "geometry": mapping(web_geom),
            }
        ],
    }


def fetch_urmia_major_rivers(raw_cache_dir: Path) -> Dict[str, Any]:
    """Fetch real river geometries in the Lake Urmia Basin from OpenStreetMap Overpass API."""
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = raw_cache_dir / "osm_urmia_rivers_raw.json"

    overpass_rivers_q = """
    [out:json][timeout:60];
    (
      way["waterway"="river"]["name"](35.75,44.35,38.45,47.65);
      relation["waterway"="river"]["name"](35.75,44.35,38.45,47.65);
    );
    out geom;
    """

    osm_payload = _query_overpass(overpass_rivers_q, timeout_sec=65)
    if osm_payload:
        cache_file.write_text(
            json.dumps(osm_payload, ensure_ascii=False), encoding="utf-8"
        )
    elif cache_file.exists():
        osm_payload = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        raise RuntimeError(
            "Unable to query OpenStreetMap Overpass API for Urmia Basin rivers."
        )

    grouped_lines: Dict[str, List[LineString]] = {r["id"]: [] for r in CANONICAL_RIVERS}

    for el in osm_payload.get("elements", []):
        tags = el.get("tags") or {}
        names_text = " ".join(
            str(tags.get(k, "")) for k in ("name", "name:fa", "name:en", "alt_name", "int_name")
        )
        if not names_text.strip():
            continue

        matched_river_id = None
        for canonical in CANONICAL_RIVERS:
            if any(kw.lower() in names_text.lower() for kw in canonical["keywords"]):
                matched_river_id = canonical["id"]
                break

        if not matched_river_id:
            continue

        if el.get("type") == "way" and el.get("geometry"):
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) >= 2:
                grouped_lines[matched_river_id].append(LineString(coords))
        elif el.get("type") == "relation" and el.get("members"):
            for mem in el["members"]:
                if mem.get("geometry"):
                    coords = [(pt["lon"], pt["lat"]) for pt in mem["geometry"]]
                    if len(coords) >= 2:
                        grouped_lines[matched_river_id].append(LineString(coords))

    features = []
    for canonical in CANONICAL_RIVERS:
        rid = canonical["id"]
        segments = grouped_lines.get(rid, [])
        if not segments:
            continue

        unioned = unary_union(segments)
        merged = linemerge(unioned) if isinstance(unioned, MultiLineString) else unioned
        simplified = ensure_valid_geometry(merged.simplify(0.0006, preserve_topology=True))
        if isinstance(simplified, LineString):
            geom_out = MultiLineString([simplified])
        elif isinstance(simplified, MultiLineString):
            geom_out = simplified
        else:
            continue

        length_km = compute_length_km(geom_out)
        if length_km < 2.0:
            continue

        features.append(
            {
                "type": "Feature",
                "id": rid,
                "properties": {
                    "id": rid,
                    "name_fa": canonical["name_fa"],
                    "name_en": canonical["name_en"],
                    "subbasin_id": canonical["subbasin"],
                    "mapped_length_km": length_km,
                    "source_lineage": "OpenStreetMap Overpass API (waterway=river)",
                },
                "geometry": mapping(geom_out),
            }
        )

    if not features:
        raise RuntimeError("Zero canonical rivers matched from OSM payload.")

    return {"type": "FeatureCollection", "features": features}