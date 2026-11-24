#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, shutil, warnings
from pathlib import Path
import geopandas as gpd
from shapely.geometry import mapping
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
CRS_G = "EPSG:4326"
CRS_M = "EPSG:32638"
PUB = ROOT / "web-dashboard" / "public" / "geo"
COPIES = [PUB, ROOT / "web-dashboard" / "dist" / "geo", ROOT / "data" / "reference" / "spatial"]
BACKUP = ROOT / "data" / "_backup_before_shoreline_clip"
TOL_M = 500.0
MIN_SEG_M = 200.0

def proj(g):
    return gpd.GeoSeries([g], crs=CRS_G).to_crs(CRS_M).iloc[0]

def unproj(g):
    return gpd.GeoSeries([g], crs=CRS_M).to_crs(CRS_G).iloc[0]

def round_coords(node, nd=5):
    if isinstance(node, (list, tuple)):
        return [round_coords(x, nd) for x in node]
    if isinstance(node, float):
        return round(node, nd)
    return node

def clean_props(row, gname):
    out = {}
    for k, v in row.items():
        if k == gname:
            continue
        if v is None:
            out[k] = None
        elif isinstance(v, float) and v != v:
            out[k] = None
        elif hasattr(v, "item"):
            out[k] = v.item()
        elif isinstance(v, (str, int, float, bool, list, dict)):
            out[k] = v
        else:
            out[k] = str(v)
    return out

def clip_lines(geom, mask):
    part = geom.intersection(mask)
    if part.is_empty:
        return part
    if part.geom_type in ("MultiLineString", "GeometryCollection"):
        segs = [g for g in part.geoms if g.geom_type == "LineString" and g.length >= MIN_SEG_M]
        if segs:
            return unary_union(segs)
    if part.geom_type == "LineString" and part.length < MIN_SEG_M:
        return part
    return part

def outside_len(path, mask):
    gdf = gpd.read_file(path).to_crs(CRS_G)
    tot = out = 0.0
    for g in gdf.geometry:
        if g is None or g.is_empty:
            continue
        gm = proj(g)
        tot += gm.length
        out += max(gm.length - gm.intersection(mask).length, 0.0)
    return tot / 1e3, out / 1e3

def grep_src():
    src = ROOT / "web-dashboard" / "src"
    hits = []
    if not src.exists():
        return hits
    for f in src.rglob("*"):
        if f.suffix.lower() not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if "data/gis" in line:
                hits.append("%s:%d  %s" % (f.relative_to(src), i, line.strip()))
    return hits

def main():
    print("=" * 78)
    print(" dashboard/src references to data/gis:")
    hits = grep_src()
    if hits:
        for h in hits:
            print("   ", h)
    else:
        print("    (none - dashboard reads only public/geo)")
    print("=" * 78)
    bnd = gpd.read_file(PUB / "urmia_lake_boundary.geojson").to_crs(CRS_M).geometry.unary_union
    mask = bnd.buffer(TOL_M)
    tight = bnd.buffer(250.0)
    spath = PUB / "urmia_shorelines.geojson"
    gdf = gpd.read_file(spath).to_crs(CRS_G)
    gname = gdf.geometry.name
    t0, o0 = outside_len(spath, tight)
    print(" BEFORE urmia_shorelines: total %.1f km | outside %.1f km (%.1f%%)" % (t0, o0, 100.0 * o0 / t0))
    BACKUP.mkdir(parents=True, exist_ok=True)
    for d in COPIES:
        t = d / spath.name
        if t.exists():
            shutil.copy2(t, BACKUP / (d.name + "__" + spath.name))
    feats = []
    for _, row in gdf.iterrows():
        g = row[gname]
        if g is None or g.is_empty:
            continue
        gm = proj(g)
        c = clip_lines(gm, mask)
        if c.is_empty:
            continue
        cg = unproj(c)
        gj = json.loads(json.dumps(mapping(cg)))
        gj["coordinates"] = round_coords(gj["coordinates"])
        feats.append({"type": "Feature", "properties": clean_props(row, gname), "geometry": gj})
    payload = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
    synced = 0
    for d in COPIES:
        t = d / spath.name
        if t.exists():
            t.write_text(payload, encoding="utf-8")
            synced += 1
    t1, o1 = outside_len(spath, tight)
    print(" AFTER  urmia_shorelines: total %.1f km | outside %.1f km (%.1f%%) | %d feats | synced %d copies" % (t1, o1, 100.0 * o1 / t1, len(feats), synced))
    print(" backup:", BACKUP)
    print("=" * 78)
    print(" FINAL CHECK - all public/geo layers vs boundary (250 m tolerance)")
    for p in sorted(PUB.glob("*.geojson")):
        if p.name == "urmia_lake_boundary.geojson":
            continue
        g = gpd.read_file(p).to_crs(CRS_G)
        geo = g.geometry.unary_union
        gm = proj(geo)
        if geo.geom_type in ("Polygon", "MultiPolygon"):
            tot = gm.area
            out = max(gm.area - gm.intersection(tight).area, 0.0)
            print("   %-40s %8.1f km2 | outside %7.2f km2 (%.1f%%)" % (p.name, tot / 1e6, out / 1e6, 100.0 * out / max(tot, 1.0)))
        else:
            tot = gm.length
            out = max(gm.length - gm.intersection(tight).length, 0.0)
            print("   %-40s %8.1f km  | outside %7.2f km  (%.1f%%)" % (p.name, tot / 1e3, out / 1e3, 100.0 * out / max(tot, 1.0)))
    print("=" * 78)

if __name__ == "__main__":
    main()
