"""
Phase 3.1c - check real Hydroweb.next STAC endpoints for Lake Urmia bbox
and inspect full CDSE hit list already saved locally.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

TIMEOUT = 40
HEADERS = {"User-Agent": "Urmia-Lake-Observatory/phase3 (research)"}
URMIA_BBOX = [44.9, 37.0, 46.0, 38.4]


def check_local_cdse():
    print("== 1) Filter local CDSE collections for exact water-level / altimetry terms ==")
    p = Path("data/raw/probe_waterlevel.json")
    if not p.is_file():
        print("   local json not found")
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    hits = data.get("cdse", {}).get("hits", [])
    strict = ("level", "lwl", "altimet", "hydro", "sentinel-3")
    matched = [
        h for h in hits
        if any(k in ((h.get("id") or "") + " " + (h.get("title") or "")).lower() for k in strict)
    ]
    print("   strict matches: %d (out of %d)" % (len(matched), len(hits)))
    for h in matched:
        print("   * %s  |  %s" % (h["id"], h["title"]))


def check_hydroweb_stac():
    print("\n== 2) Probe real Hydroweb.next STAC endpoints ==")
    candidates = [
        "https://hydroweb.next.theia-land.fr/api/v1/rs-catalog/stac",
        "https://hydroweb.next.theia-land.fr/api/catalog/stac",
        "https://hydroweb.next.theia-land.fr/api/v1/rs-catalog/stac/collections",
    ]
    working_root = None
    for u in candidates:
        try:
            r = requests.get(u, timeout=TIMEOUT, headers=HEADERS)
            ct = r.headers.get("Content-Type", "")
            print("   [%s] %s  (%s)" % (r.status_code, u, ct[:45]))
            if r.status_code == 200 and "json" in ct.lower() and working_root is None:
                if u.endswith("/collections"):
                    working_root = u[:-len("/collections")]
                else:
                    working_root = u
        except requests.RequestException as exc:
            print("   [ERR] %s -> %s" % (u, exc))

    if not working_root:
        print("   no public STAC root responded with JSON")
        return

    print("\n== 3) List lake collections on:", working_root)
    r = requests.get(working_root + "/collections", timeout=TIMEOUT, headers=HEADERS)
    if r.status_code == 200:
        cols = r.json().get("collections", [])
        print("   total collections: %d" % len(cols))
        for c in cols:
            cid = c.get("id", "")
            if any(k in cid.upper() for k in ("LAKE", "HYDROWEB", "WATER", "LWL", "S3")):
                print("   * %s  |  %s" % (cid, c.get("title", "")))

    print("\n== 4) Search Urmia bbox in HYDROWEB_LAKES_OPE & HYDROWEB_LAKES_RESEARCH ==")
    search_url = working_root + "/search"
    for col in ("HYDROWEB_LAKES_OPE", "HYDROWEB_LAKES_RESEARCH"):
        payload = {"collections": [col], "bbox": URMIA_BBOX, "limit": 10}
        sr = requests.post(search_url, json=payload, timeout=TIMEOUT, headers=HEADERS)
        print("   [%s] search %s" % (sr.status_code, col))
        if sr.status_code == 200:
            feats = sr.json().get("features", [])
            print("        features found: %d" % len(feats))
            for f in feats:
                fid = f.get("id")
                props = f.get("properties", {})
                assets = f.get("assets", {})
                print("        - id=%s | start=%s | end=%s" % (
                    fid,
                    props.get("start_datetime"),
                    props.get("end_datetime"),
                ))
                for ak, av in list(assets.items())[:4]:
                    href = av.get("href", "")
                    print("          asset[%s]: %s" % (ak, href[:95]))
                    if href.startswith("http"):
                        hr = requests.get(href, timeout=20, headers=HEADERS, stream=True)
                        print("             GET -> [%s] (%s)" % (
                            hr.status_code,
                            hr.headers.get("Content-Type", "")[:40],
                        ))
                        hr.close()


def main():
    check_local_cdse()
    check_hydroweb_stac()
    return 0


if __name__ == "__main__":
    sys.exit(main())