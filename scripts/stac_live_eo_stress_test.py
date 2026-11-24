#!/usr/bin/env python3
"""
TerraScope Phase 4 - Full-Basin Mosaic Live EO STAC Connector & Stress Benchmark
Stitches multi-granule Sentinel-2 L2A scenes (T38SNJ, T38SNH, T38SMJ, T38SMH) over Lake Urmia
"""

from __future__ import annotations

import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import planetary_computer
import pystac_client
from requests import Session as HttpSession

URMIA_BBOX = [44.95, 37.00, 45.95, 38.30]
MOSAIC_BOUNDS = [44.80, 36.85, 46.15, 38.45]
STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
DATA_API_URL = "https://planetarycomputer.microsoft.com/api/data/v1"
OUTPUT_JSON = Path("web-dashboard/public/data/urmia_live_stac_feed.json")


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def register_basin_mosaic(http: HttpSession, date_range: str) -> dict[str, str]:
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": MOSAIC_BOUNDS,
        "datetime": date_range,
        "query": {"eo:cloud_cover": {"lt": 20}},
    }
    resp = http.post(f"{DATA_API_URL}/mosaic/register", json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    search_id = data.get("searchid") or data.get("id")
    if not search_id:
        raise RuntimeError(f"Mosaic registration returned unexpected payload: {data}")

    rgb_url = (
        f"{DATA_API_URL}/mosaic/{search_id}/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x"
        f"?collection=sentinel-2-l2a&assets=visual&format=webp"
    )
    ndwi_url = (
        f"{DATA_API_URL}/mosaic/{search_id}/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x"
        f"?collection=sentinel-2-l2a&expression=(B03-B08)/(B03%2BB08)"
        f"&asset_as_band=true&rescale=-0.6,0.6&colormap_name=ylgnbu&format=webp"
    )
    return {
        "search_id": search_id,
        "true_color_webp": rgb_url,
        "ndwi_live_webp": ndwi_url,
    }


def fetch_single_tile(http: HttpSession, url: str) -> tuple[int, float, int]:
    t0 = time.perf_counter()
    resp = http.get(url, timeout=20)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return resp.status_code, elapsed_ms, len(resp.content)


def run_stac_stress_test(concurrency: int = 9, zoom: int = 9) -> dict[str, Any]:
    print("=== TerraScope Full-Basin Mosaic STAC Stress Test ===")
    t_query_start = time.perf_counter()

    catalog = pystac_client.Client.open(
        STAC_API_URL,
        modifier=planetary_computer.sign_inplace,
    )

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=90)
    date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=URMIA_BBOX,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": 20}},
        max_items=12,
    )
    items = sorted(
        list(search.items()),
        key=lambda it: it.datetime or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    stac_latency_ms = round((time.perf_counter() - t_query_start) * 1000.0, 2)

    if not items:
        raise RuntimeError("No Sentinel-2 scene (<20% cloud) found in the last 90 days.")

    center_x, center_y = deg2num(37.65, 45.45, zoom)
    test_coords = [
        (zoom, center_x + dx, center_y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
    ]

    latencies: list[float] = []
    payload_bytes: list[int] = []
    ok_count = 0

    with HttpSession() as http:
        mosaic_info = register_basin_mosaic(http, date_range)
        sample_urls = [
            mosaic_info["true_color_webp"].format(z=z, x=x, y=y)
            for (z, x, y) in test_coords
        ]
        ndwi_probe_url = mosaic_info["ndwi_live_webp"].format(
            z=zoom, x=center_x, y=center_y
        )

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(fetch_single_tile, http, u) for u in sample_urls]
            for fut in as_completed(futures):
                status, ms, size_b = fut.result()
                if status == 200:
                    ok_count += 1
                    latencies.append(ms)
                    payload_bytes.append(size_b)

        ndwi_status, ndwi_ms, ndwi_bytes = fetch_single_tile(http, ndwi_probe_url)

    p50_ms = round(statistics.median(latencies), 2) if latencies else -1.0
    p95_ms = (
        round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 2)
        if latencies
        else -1.0
    )
    avg_kb = round((sum(payload_bytes) / max(1, len(payload_bytes))) / 1024.0, 2)

    tile_set = {
        "true_color_webp": mosaic_info["true_color_webp"],
        "ndwi_live_webp": mosaic_info["ndwi_live_webp"],
    }

    scenes_payload = []
    for item in items[:6]:
        scenes_payload.append(
            {
                "id": item.id,
                "mgrs_tile": item.properties.get("s2:mgrs_tile", ""),
                "datetime": item.datetime.isoformat() if item.datetime else None,
                "cloud_cover": round(float(item.properties.get("eo:cloud_cover", 0.0)), 2),
                "platform": item.properties.get("platform", "sentinel-2"),
                "bbox": MOSAIC_BOUNDS,
                "geometry": item.geometry,
                "tiles": tile_set,
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "basin": "Lake Urmia",
        "mosaic_search_id": mosaic_info["search_id"],
        "mosaic_bounds": MOSAIC_BOUNDS,
        "benchmark": {
            "stac_search_latency_ms": stac_latency_ms,
            "tiles_tested": len(sample_urls),
            "tiles_succeeded": ok_count,
            "ndwi_probe_status": ndwi_status,
            "ndwi_probe_ms": round(ndwi_ms, 2),
            "tile_p50_ms": p50_ms,
            "tile_p95_ms": p95_ms,
            "avg_tile_size_kb": avg_kb,
            "webp_optimized": True,
            "ui_frame_budget_safe": ok_count == len(sample_urls) and ndwi_status == 200 and avg_kb < 120,
        },
        "latest_scene": scenes_payload[0],
        "recent_scenes": scenes_payload,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report["benchmark"], ensure_ascii=False, indent=2))
    mgrs_list = sorted({s["mgrs_tile"] for s in scenes_payload if s["mgrs_tile"]})
    print(f"Mosaic ID: {mosaic_info['search_id']} | Granules stitched: {mgrs_list}")
    print(f"Latest Pass: {scenes_payload[0]['id']} | Cloud: {scenes_payload[0]['cloud_cover']}%")
    print(f"Saved feed -> {OUTPUT_JSON}")
    return report


if __name__ == "__main__":
    run_stac_stress_test()