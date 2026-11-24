#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, json
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
CRS_G = "EPSG:4326"
CRS_M = "EPSG:32638"

SETS = [
    ("A public/geo", ROOT / "web-dashboard" / "public" / "geo"),
    ("B dist/geo", ROOT / "web-dashboard" / "dist" / "geo"),
    ("C data/reference", ROOT / "data" / "reference" / "spatial"),
]

def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()[:10]

def geom_of(p):
    g = gpd.read_file(p).to_crs(CRS_G)
    return g.geometry.unary_union

def proj(g):
    return gpd.GeoSeries([g], crs=CRS_G).to_crs(CRS_M).iloc[0]

def show_scripts():
    p = ROOT / "web-dashboard" / "package.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        print(" SCRIPTS:", d.get("scripts"))
    for cfg in ("vite.config.ts", "vite.config.js", "astro.config.mjs", "next.config.js"):
        q = ROOT / "web-dashboard" / cfg
        if q.exists():
            print(" CONFIG:", cfg)

def show_set(label, d):
    print("-" * 78)
    print(" SET", label, "->", d)
    if not d.exists():
        print("   MISSING DIRECTORY")
        return
    for p in sorted(d.glob("*.geojson")):
        try:
            g = geom_of(p)
            m = proj(g)
            b = g.bounds
            print("   %-40s %s A%8.1f km2 L%7.1f km W%.4f S%.4f E%.4f N%.4f" % (p.name, md5(p), m.area/1e6, m.length/1e3, b[0], b[1], b[2], b[3]))
        except Exception as e:
            print("   %-40s READ ERROR %s" % (p.name, e))

def compare(name, a, b, la, lb):
    if not (a.exists() and b.exists()):
        print("   %-40s only in %s" % (name, la if a.exists() else lb))
        return
    if md5(a) == md5(b):
        print("   %-40s IDENTICAL" % name)
        return
    g1 = proj(geom_of(a))
    g2 = proj(geom_of(b))
    sym = g1.symmetric_difference(g2)
    print("   %-40s DIFFERS  A1 %8.1f A2 %8.1f  symdiff %9.2f km2" % (name, g1.area/1e6, g2.area/1e6, sym.area/1e6))

def main():
    show_scripts()
    print("=" * 78)
    for label, d in SETS:
        show_set(label, d)
    a = SETS[0][1]
    b = SETS[1][1]
    print("=" * 78)
    print(" DIST vs PUBLIC (served copy vs source)")
    names = sorted({p.name for p in a.glob("*.geojson")} | {p.name for p in b.glob("*.geojson")}) if a.exists() and b.exists() else []
    for n in names:
        compare(n, a / n, b / n, "public/geo", "dist/geo")
    print("=" * 78)

if __name__ == "__main__":
    main()
