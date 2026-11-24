"""
Phase 3.1 - probe open data endpoints for Lake Urmia.
Only reports HTTP status + short preview. Writes nothing to data/ except the report.
Run: python scripts/probe_sources.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

LAKE = {
    "name": "Lake Urmia",
    "lat": 37.70,
    "lon": 45.35,
    "clms_lake_id": "1300000000142",
    "grealm_id_north": 115,
}
TIMEOUT = 40
HEADERS = {"User-Agent": "Taraz-Environmental-Platform/phase3 (research; contact: admin)"}

CANDIDATES = [
    {
        "id": "nasa_power_daily",
        "kind": "climate",
        "expect": "JSON with properties.parameter.T2M",
        "url": (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            "?parameters=T2M,PRECTOTCORR&community=AG"
            "&longitude=45.35&latitude=37.70"
            "&start=20240101&end=20240131&format=JSON"
        ),
    },
    {
        "id": "open_meteo_era5_archive",
        "kind": "climate",
        "expect": "JSON with daily.time",
        "url": (
            "https://archive-api.open-meteo.com/v1/archive"
            "?latitude=37.70&longitude=45.35"
            "&start_date=2024-01-01&end_date=2024-01-31"
            "&daily=temperature_2m_mean,precipitation_sum&timezone=UTC"
        ),
    },
    {
        "id": "usda_grealm_chart_page",
        "kind": "waterlevel",
        "expect": "HTML page (200) or 404 - tells us if regionid/reservoir_name is right",
        "url": (
            "https://ipad.fas.usda.gov/cropexplorer/global_reservoir/"
            "gr_regional_chart.aspx?regionid=me&reservoir_name=Urmia"
        ),
    },
    {
        "id": "usda_grealm_data_page",
        "kind": "waterlevel",
        "expect": "HTML or plain text",
        "url": "https://ipad.fas.usda.gov/cropexplorer/global_reservoir/",
    },
    {
        "id": "cdse_stac",
        "kind": "stac",
        "expect": "JSON STAC landing page",
        "url": "https://catalogue.dataspace.copernicus.eu/stac",
    },
    {
        "id": "hydroweb_next_root",
        "kind": "waterlevel",
        "expect": "200 JSON => open; 401/403 => token required",
        "url": "https://hydroweb.next.theia-land.fr/api/",
    },
]


def probe(item):
    started = time.time()
    result = {
        "id": item["id"],
        "kind": item["kind"],
        "url": item["url"],
        "expect": item["expect"],
        "status": None,
        "content_type": None,
        "elapsed_s": None,
        "preview": None,
        "error": None,
        "json_ok": False,
    }
    try:
        resp = requests.get(item["url"], timeout=TIMEOUT, headers=HEADERS)
        result["status"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")
        result["elapsed_s"] = round(time.time() - started, 2)
        body = resp.text or ""
        result["preview"] = " ".join(body[:400].split())
        if "json" in (result["content_type"] or "") or body.lstrip().startswith("{"):
            try:
                json.loads(body)
                result["json_ok"] = True
            except json.JSONDecodeError as exc:
                result["error"] = "json decode: %s" % exc
    except requests.RequestException as exc:
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
        result["elapsed_s"] = round(time.time() - started, 2)
    return result


def main():
    print("# probe for %s  lat=%s lon=%s" % (LAKE["name"], LAKE["lat"], LAKE["lon"]))
    print("# clms_lake_id=%s  grealm_north_id=%s\n" % (LAKE["clms_lake_id"], LAKE["grealm_id_north"]))

    rows = []
    for item in CANDIDATES:
        row = probe(item)
        rows.append(row)
        status = row["status"] if row["status"] is not None else "ERR"
        print("[%s] %-24s %ss  json=%s" % (status, row["id"], row["elapsed_s"], row["json_ok"]))
        if row["error"]:
            print("        error: %s" % row["error"])
        if row["preview"]:
            print("        preview: %s" % row["preview"][:220])
        print()

    ok = [r for r in rows if r["status"] == 200]
    print("# reachable: %d/%d" % (len(ok), len(rows)))

    out = Path("data/raw")
    if out.is_dir():
        report = out / "probe_report.json"
        report.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("# saved: %s" % report)
    else:
        print("# data/raw not found - report not saved (run from repo root)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
