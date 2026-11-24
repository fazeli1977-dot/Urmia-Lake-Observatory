"""
Phase 3.1b - find a reachable water-level source for Lake Urmia.
G-REALM (USDA IPAD) is retired -> 503. This script probes only; it writes one report.
Run: python scripts\probe_waterlevel.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

TIMEOUT = 40
HEADERS = {"User-Agent": "Urmia-Lake-Observatory/phase3 (research)"}
KEYWORDS = ("lake", "water", "level", "altimet", "hydro", "reservoir")


def get(url, as_json=False):
    t0 = time.time()
    rec = {"url": url, "status": None, "elapsed_s": None, "note": None, "body": None, "text": ""}
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        rec["status"] = r.status_code
        rec["elapsed_s"] = round(time.time() - t0, 2)
        rec["text"] = r.text or ""
        if as_json:
            try:
                rec["body"] = r.json()
            except ValueError:
                rec["note"] = "not json: " + " ".join(rec["text"][:160].split())
        else:
            rec["note"] = " ".join(rec["text"][:160].split())
    except requests.RequestException as exc:
        rec["note"] = "%s: %s" % (type(exc).__name__, exc)
        rec["elapsed_s"] = round(time.time() - t0, 2)
    return rec


def task_cdse():
    print("== A) CDSE STAC collections matching:", ", ".join(KEYWORDS))
    rec = get("https://catalogue.dataspace.copernicus.eu/stac/collections?limit=1000", as_json=True)
    print("   [%s] %ss" % (rec["status"], rec["elapsed_s"]))
    hits = []
    body = rec["body"]
    if isinstance(body, dict):
        cols = body.get("collections") or []
        print("   collections returned: %d" % len(cols))
        for c in cols:
            blob = ("%s %s %s" % (c.get("id", ""), c.get("title", ""), c.get("description", ""))).lower()
            if any(k in blob for k in KEYWORDS):
                hits.append({"id": c.get("id"), "title": c.get("title")})
        for h in hits[:25]:
            print("   * %s  |  %s" % (h["id"], h["title"]))
        print("   matches: %d" % len(hits))
    elif rec["note"]:
        print("   note:", rec["note"])
    return {"status": rec["status"], "hits": hits}


def task_hydroweb_paths():
    print("\n== B) hydroweb.next: extract /api/ paths from its own page + JS bundles")
    found = set()
    home = get("https://hydroweb.next.theia-land.fr/")
    print("   home: [%s]" % home["status"])
    if home["text"]:
        for m in re.findall(r'"(/api/[A-Za-z0-9_\-/\.]{2,70})"', home["text"]):
            found.add(m)
        for m in re.findall(r'(https://hydroweb\.next\.theia-land\.fr/api/[A-Za-z0-9_\-/\.]{2,70})', home["text"]):
            found.add(m)
        chunks = re.findall(r'src="(/_next/static/[^"]+\.js)"', home["text"])[:6]
        print("   js chunks scanned: %d" % len(chunks))
        for chunk in chunks:
            js = get("https://hydroweb.next.theia-land.fr" + chunk)
            for m in re.findall(r'(/api/[A-Za-z0-9_\-/\.]{2,70})', js["text"] or ""):
                found.add(m)
    for p in sorted(found):
        print("   discovered:", p)
    if not found:
        print("   nothing found")
    return sorted(found)


def task_candidates(discovered):
    print("\n== C) candidate water-level endpoints")
    urls = [
        "https://hydroweb.next.theia-land.fr/api/",
        "https://hydroweb.next.theia-land.fr/api/collections",
        "https://hydroweb.next.theia-land.fr/api/lakes",
        "https://hydroweb.next.theia-land.fr/api/time_series",
        "https://dahiti.dgfi.tum.de/api/v1/",
        "https://ipad.fas.usda.gov/",
    ]
    for p in discovered:
        full = p if p.startswith("http") else "https://hydroweb.next.theia-land.fr" + p
        if full not in urls:
            urls.append(full)

    rows = []
    for u in urls:
        rec = get(u)
        row = {"url": u, "status": rec["status"], "elapsed_s": rec["elapsed_s"], "note": rec["note"]}
        rows.append(row)
        print("   [%s] %-58s %ss" % (rec["status"], u[:58], rec["elapsed_s"]))
        if rec["note"]:
            print("          ", rec["note"][:150])
    return rows


def main():
    out_dir = Path("data/raw")
    report = {}
    report["cdse"] = task_cdse()
    report["hydroweb_paths"] = task_hydroweb_paths()
    report["candidates"] = task_candidates(report["hydroweb_paths"])

    ok = [r for r in report["candidates"] if r["status"] == 200]
    print("\n# reachable candidates: %d/%d" % (len(ok), len(report["candidates"])))

    if out_dir.is_dir():
        path = out_dir / "probe_waterlevel.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("# saved: %s" % path)
    else:
        print("# data/raw not found - report not saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
