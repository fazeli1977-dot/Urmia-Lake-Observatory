"""
Phase 3.1d - Check CLMS Water Level Lakes Global V2 GeoJSON for Lake Urmia
and inspect Hydroweb STAC feature properties.
"""
from __future__ import annotations

import json
import sys
import requests

TIMEOUT = 40
HEADERS = {"User-Agent": "Urmia-Lake-Observatory/phase3 (research)"}
URMIA_BBOX = [44.9, 37.0, 46.0, 38.4]


def check_clms_wl():
    print("== 1) Search CDSE clms_wl-lakes_global_vector_daily_v2_geojson for Urmia ==")
    url = "https://stac.dataspace.copernicus.eu/v1/search"
    payload = {
        "collections": ["clms_wl-lakes_global_vector_daily_v2_geojson"],
        "bbox": URMIA_BBOX,
        "limit": 5,
    }
    r = requests.post(url, json=payload, timeout=TIMEOUT, headers=HEADERS)
    print("   [%s] POST %s" % (r.status_code, url))
    if r.status_code != 200:
        print("   body:", r.text[:300])
        return
    feats = r.json().get("features", [])
    print("   features found (with Urmia bbox): %d" % len(feats))

    if not feats:
        print("   (Trying global search without bbox - product may have global bbox)")
        r2 = requests.post(
            url,
            json={"collections": ["clms_wl-lakes_global_vector_daily_v2_geojson"], "limit": 3},
            timeout=TIMEOUT,
            headers=HEADERS,
        )
        feats = r2.json().get("features", [])
        print("   features found (global): %d" % len(feats))

    for f in feats[:3]:
        print("   - id=%s | datetime=%s | bbox=%s" % (
            f.get("id"),
            f.get("properties", {}).get("datetime"),
            f.get("bbox"),
        ))
        for ak, av in f.get("assets", {}).items():
            href = av.get("href", "")
            print("     asset[%s]: %s" % (ak, href[:105]))
            alt = av.get("alternate", {})
            if alt:
                print("     alternates:", list(alt.keys()))
            if href.startswith("http"):
                hr = requests.get(href, timeout=25, headers=HEADERS, stream=True)
                ct = hr.headers.get("Content-Type", "")
                cl = hr.headers.get("Content-Length", "?")
                print("        GET -> [%s] ct=%s len=%s" % (hr.status_code, ct[:40], cl))
                if hr.status_code == 200 and ("json" in ct.lower() or href.endswith(".geojson")):
                    chunk = next(hr.iter_content(chunk_size=600), b"").decode("utf-8", errors="replace")
                    print("        sample:", chunk[:250].replace("\n", " "))
                hr.close()


def check_hydroweb_props():
    print("\n== 2) Inspect full STAC properties of Hydroweb L_urmia ==")
    url = "https://hydroweb.next.theia-land.fr/api/v1/rs-catalog/stac/search"
    r = requests.post(
        url,
        json={"collections": ["HYDROWEB_LAKES_OPE"], "bbox": URMIA_BBOX, "limit": 1},
        timeout=TIMEOUT,
        headers=HEADERS,
    )
    if r.status_code == 200:
        feats = r.json().get("features", [])
        if feats:
            f = feats[0]
            print("   properties keys:", sorted(f.get("properties", {}).keys()))
            print("   properties JSON:", json.dumps(f.get("properties", {}), ensure_ascii=False)[:900])
            print("   assets keys:", list(f.get("assets", {}).keys()))


if __name__ == "__main__":
    check_clms_wl()
    check_hydroweb_props()
    sys.exit(0)