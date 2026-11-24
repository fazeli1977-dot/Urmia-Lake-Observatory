#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path
import geopandas as gpd
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
CRS_G = "EPSG:4326"
CRS_M = "EPSG:32638"
BACKUP = ROOT / "data" / "_backup_before_clip"
MIN_PART_KM2 = 0.25

REF_FILE = ROOT / "web-dashboard" / "public" / "geo" / "urmia_lake_boundary.geojson"

GROUPS = [
    ("public/geo", ROOT / "web-dashboard" / "public" / "geo", [
        ("urmia_active_water.geojson", "area", 100.0),
        ("urmia_desiccated_zones.geojson", "area", 100.0),
        ("urmia_shorelines.geojson", "length", 250.0),
        ("urmia_hypsometric_contours.geojson", "length", 250.0),
    ]),
    ("public/data/gis", ROOT / "web-dashboard" / "public" / "data" / "gis", [
        ("lake_water_extent.geojson", "area", 100.0),
        ("salt_crust_exposure.geojson", "area", 100.0),
        ("historical_shorelines.geojson", "length", 250.0),
        ("bathymetric_contours.geojson", "length", 250.0),
    ]),
]

MIRRORS = {
    "public/geo": [ROOT / "data" / "reference" / "spatial", ROOT / "web-dashboard" / "dist" / "geo"],
    "public/data/gis": [ROOT / "data" / "processed" / "gis", ROOT / "web-dashboard" / "dist" / "data" / "gis"],
}

def project(geom):
    return gpd.GeoSeries([geom], crs=CRS_G).to_crs(CRS_M).iloc[0]

def unproject(geom):
    return gpd.GeoSeries([geom], crs=CRS_M).to_crs(CRS_G).iloc[0]

def round_coords(node, nd=5):
    if isinstance(node, (list, tuple)):
        return [round_coords(x, nd) for x in node]
    if isinstance(node, float):
        return round(node, nd)
    return node

def features(gdf):
    gname = gdf.geometry.name
    for _, row in gdf.iterrows():
        geom = row[gname]
        if geom is None or geom.is_empty:
            continue
        props = {}
        for k, v in row.items():
            if k == gname:
                continue
            if v is None or (isinstance(v, float) and v != v):
                props[k] = None
            elif hasattr(v, "tolist"):
                props[k] = v.tolist()
            elif hasattr(v, "item"):
                props[k] = v.item()
            elif isinstance(v, (str, int, float, bool, list, dict)):
                props[k] = v
            else:
                props[k] = str(v)
        yield props, geom

def load_union_m(p):
    gdf = gpd.read_file(p).to_crs(CRS_G)
    geoms = [project(g) for _, g in features(gdf)]
    return unary_union(geoms), len(geoms)

def bbox_deg(geom_m):
    b = unproject(geom_m).bounds
    return "[W %.4f, S %.4f, E %.4f, N %.4f]" % (b[0], b[1], b[2], b[3])

def best_shift(water_m, ref_m, max_m=4000.0, step_m=500.0):
    ws = water_m.simplify(80.0, preserve_topology=True)
    rs = ref_m.simplify(80.0, preserve_topology=True)
    base = ws.difference(rs).area
    best = (0.0, 0.0, base)
    steps = int(max_m // step_m)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx, dy = i * step_m, j * step_m
            area = translate(ws, dx, dy).difference(rs).area
            if area < best[2]:
                best = (dx, dy, area)
    return best, base

def scan_frontend_refs():
    src = ROOT / "web-dashboard" / "src"
    found = set()
    if src.exists():
        for f in src.rglob("*.*"):
            if f.suffix.lower() in (".ts", ".tsx", ".js", ".jsx", ".json"):
                txt = f.read_text(encoding="utf-8", errors="ignore")
                for m in re.findall(r"[A-Za-z0-9_./-]+\.geojson", txt):
                    found.add(f"{f.relative_to(src)} -> {m}")
    return sorted(found)

def clean(geom, mode):
    if geom.is_empty:
        return geom
    parts = list(geom.geoms) if geom.geom_type in ("MultiPolygon", "MultiLineString", "GeometryCollection") else [geom]
    if mode == "area":
        parts = [p for p in parts if p.geom_type in ("Polygon", "MultiPolygon") and p.area / 1e6 >= MIN_PART_KM2]
    if not parts:
        return geom.buffer(0).intersection(geom)
    merged = unary_union(parts)
    if mode == "area" and merged.geom_type == "Polygon":
        merged = MultiPolygon([merged])
    return merged

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print("=" * 78)
    print(" FRONTEND GEOJSON REFERENCES IN web-dashboard/src:")
    for r in scan_frontend_refs():
        print("   ", r)
    print("=" * 78)
    ref, nref = load_union_m(REF_FILE)
    print(" REF urmia_lake_boundary.geojson (%d feat): %.1f km2  %s" % (nref, ref.area / 1e6, bbox_deg(ref)))
    for gname, gdir, targets in GROUPS:
        print("-" * 78)
        print(" GROUP:", gname)
        wpath = gdir / targets[0][0]
        if wpath.exists():
            wm, nw = load_union_m(wpath)
            (sdx, sdy, sarea), base = best_shift(wm, ref)
            print("   WATER (%d feat): %.1f km2  %s" % (nw, wm.area / 1e6, bbox_deg(wm)))
            print("   outside ref: %.2f km2 (%.1f%%) | best shift dx=%+.0fm dy=%+.0fm -> %.2f km2" % (base/1e6, 100*base/max(wm.area,1), sdx, sdy, sarea/1e6))
        for fname, mode, tol in targets:
            p = gdir / fname
            if not p.exists():
                continue
            gdf = gpd.read_file(p).to_crs(CRS_G)
            ref_buf = ref.buffer(tol)
            total = outside = 0.0
            new_feats = []
            for props, geom in features(gdf):
                gm = project(geom)
                keep = gm.intersection(ref_buf)
                if mode == "area":
                    total += gm.area
                    outside += max(gm.area - keep.area, 0.0)
                else:
                    total += gm.length
                    outside += max(gm.length - keep.length, 0.0)
                if args.apply:
                    keep = clean(keep, mode)
                    if keep.is_empty:
                        continue
                    gj = json.loads(json.dumps(mapping(unproject(keep))))
                    gj["coordinates"] = round_coords(gj["coordinates"])
                    new_feats.append({"type": "Feature", "properties": props, "geometry": gj})
            scale = 1e6 if mode == "area" else 1e3
            unit = "km2" if mode == "area" else "km"
            ratio = 100.0 * outside / total if total else 0.0
            print("   %-36s total %8.1f %-3s | outside %8.2f %-3s (%5.1f%%)" % (fname, total/scale, unit, outside/scale, unit, ratio))
            if args.apply and outside > 0:
                bdir = BACKUP / gname.replace("/", "_")
                bdir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, bdir / fname)
                payload = json.dumps({"type": "FeatureCollection", "features": new_feats}, ensure_ascii=False, separators=(",", ":"))
                p.write_text(payload, encoding="utf-8")
                for mdir in MIRRORS.get(gname, []):
                    if mdir.exists() and (mdir / fname).exists():
                        (mdir / fname).write_text(payload, encoding="utf-8")
                print("     [CLIPPED & SYNCED] %d features" % len(new_feats))
    print("=" * 78)

if __name__ == "__main__":
    main()
