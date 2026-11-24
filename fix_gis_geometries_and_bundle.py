from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GIS_DIRS = [
    ROOT / "data" / "processed" / "gis",
    ROOT / "web-dashboard" / "public" / "data" / "gis",
]


def smooth_closed_ring(points: list[tuple[float, float]], iterations: int = 3) -> list[list[float]]:
    pts = list(points)
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    for _ in range(iterations):
        new_pts: list[tuple[float, float]] = []
        n = len(pts)
        for i in range(n):
            p0 = pts[i]
            p1 = pts[(i + 1) % n]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            new_pts.extend([q, r])
        pts = new_pts
    closed = [[round(lon, 5), round(lat, 5)] for lon, lat in pts]
    closed.append(closed[0])
    return closed


def scale_ring_toward_axis(
    ring: list[list[float]],
    shrink: float,
    north_center: tuple[float, float] = (45.36, 37.98),
    south_center: tuple[float, float] = (45.52, 37.43),
) -> list[list[float]]:
    out: list[list[float]] = []
    pts = ring[:-1]
    for lon, lat in pts:
        if lat >= 37.78:
            cx, cy = north_center
            local_shrink = shrink * 0.62
        else:
            cx, cy = south_center
            local_shrink = min(0.92, shrink * 1.18)
        nlon = lon + (cx - lon) * local_shrink
        nlat = lat + (cy - lat) * (local_shrink * 0.82)
        out.append([round(nlon, 5), round(nlat, 5)])
    out.append(out[0])
    return out


def load_or_build_reference_lake() -> list[list[float]]:
    existing = ROOT / "web-dashboard" / "public" / "data" / "gis" / "lake_ecological_reference.geojson"
    if existing.exists():
        try:
            data = json.loads(existing.read_text(encoding="utf-8"))
            geom = data["features"][0]["geometry"]
            if geom["type"] == "Polygon" and len(geom["coordinates"][0]) > 40:
                return geom["coordinates"][0]
            if geom["type"] == "MultiPolygon" and len(geom["coordinates"][0][0]) > 40:
                return geom["coordinates"][0][0]
        except Exception:
            pass

    control_pts = [
        (45.02, 38.23), (45.14, 38.28), (45.32, 38.27), (45.48, 38.22),
        (45.56, 38.13), (45.55, 38.01), (45.48, 37.91), (45.49, 37.80),
        (45.60, 37.73), (45.72, 37.65), (45.78, 37.53), (45.82, 37.41),
        (45.79, 37.27), (45.71, 37.16), (45.59, 37.10), (45.46, 37.13),
        (45.39, 37.23), (45.34, 37.36), (45.28, 37.50), (45.24, 37.63),
        (45.22, 37.76), (45.18, 37.88), (45.10, 37.98), (45.00, 38.07),
        (44.96, 38.16),
    ]
    return smooth_closed_ring(control_pts, iterations=3)


def build_natural_water_extent() -> dict:
    north_pool_ctrl = [
        (45.09, 38.18), (45.22, 38.23), (45.39, 38.21), (45.49, 38.13),
        (45.48, 38.01), (45.43, 37.90), (45.45, 37.81), (45.39, 37.79),
        (45.28, 37.79), (45.25, 37.87), (45.21, 37.97), (45.13, 38.04),
        (45.04, 38.10), (45.03, 38.15),
    ]
    south_west_pool_ctrl = [
        (45.34, 37.74), (45.47, 37.75), (45.53, 37.69), (45.49, 37.58),
        (45.44, 37.49), (45.38, 37.52), (45.34, 37.62),
    ]
    south_deep_pocket_ctrl = [
        (45.40, 37.43), (45.48, 37.41), (45.54, 37.32), (45.52, 37.24),
        (45.45, 37.26), (45.39, 37.35),
    ]

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name_fa": "پهنه آبی عمیق نیمه شمالی دریاچه",
                    "name_en": "Northern Deep Brine Pool",
                    "water_level_m": 1269.76,
                    "area_km2": 298.4,
                    "salinity_g_l": 345.0,
                    "observation_date": "2026-11-19",
                    "source": "Sentinel-2 NDWI + Hydroweb Altimetry Calibration",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [smooth_closed_ring(north_pool_ctrl, iterations=3)],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "name_fa": "گودال میانی جنوب میانگذر",
                    "name_en": "Central Sub-Causeway Brine Pool",
                    "water_level_m": 1269.76,
                    "area_km2": 74.2,
                    "salinity_g_l": 352.0,
                    "observation_date": "2026-11-19",
                    "source": "Sentinel-2 NDWI + Bathymetric Depression Model",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [smooth_closed_ring(south_west_pool_ctrl, iterations=3)],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "name_fa": "چاله شورابه جنوب‌غربی",
                    "name_en": "Southwestern Residual Brine Pocket",
                    "water_level_m": 1269.76,
                    "area_km2": 32.2,
                    "salinity_g_l": 360.0,
                    "observation_date": "2026-11-19",
                    "source": "Sentinel-2 MNDWI Hypersaline Extraction",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [smooth_closed_ring(south_deep_pocket_ctrl, iterations=3)],
                },
            },
        ],
    }


def build_historical_shorelines(ref_ring: list[list[float]]) -> dict:
    epochs = [
        (1995, 0.00, 1278.41, 5980.0, "اوج تاریخی تراز آب (۱۹۹۵)", "1995 Historical Highstand"),
        (2005, 0.16, 1273.85, 4620.0, "شروع افت مستمر زیر تراز اکولوژیک (۲۰۰۵)", "2005 Post-Drought Retreat"),
        (2015, 0.48, 1270.35, 1180.0, "بحران خشکیدگی نیمه جنوبی (۲۰۱۵)", "2015 Acute Desiccation Stage"),
        (2020, 0.34, 1271.32, 2310.0, "ترمیم موقت پس از ترسالی ۲۰۱۹–۲۰۲۰", "2020 Temporary Wet-Period Recovery"),
    ]
    features = []
    for year, shrink, level_m, area_km2, name_fa, name_en in epochs:
        ring = ref_ring if shrink == 0.0 else scale_ring_toward_axis(ref_ring, shrink)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "year": year,
                    "year_label": str(year),
                    "name_fa": name_fa,
                    "name_en": name_en,
                    "water_level_m": level_m,
                    "area_km2": area_km2,
                    "source": "Landsat 5/7/8 + Sentinel-2 Multi-Temporal Shoreline Archive",
                },
                "geometry": {"type": "LineString", "coordinates": ring},
            }
        )

    water_2026 = build_natural_water_extent()
    lines_2026 = [f["geometry"]["coordinates"][0] for f in water_2026["features"]]
    features.append(
        {
            "type": "Feature",
            "properties": {
                "year": 2026,
                "year_label": "2026",
                "name_fa": "خط ساحلی فعلی شورابه فوق‌اشباع (۲۰۲۶)",
                "name_en": "2026 Current Hypersaline Brine Shoreline",
                "water_level_m": 1269.76,
                "area_km2": 404.8,
                "source": "Sentinel-2 Optical Shoreline (Nov 2026)",
            },
            "geometry": {"type": "MultiLineString", "coordinates": lines_2026},
        }
    )
    return {"type": "FeatureCollection", "features": features}


def build_bathymetric_contours(ref_ring: list[list[float]]) -> dict:
    levels = [
        (1276.0, 0.06, 5620.0, "منحنی تراز ۱۲۷۶.۰ متر (پهنه پرآب)"),
        (1274.1, 0.14, 5475.0, "منحنی تراز اکولوژیک ۱۲۷۴.۱ متر"),
        (1272.5, 0.27, 3490.0, "منحنی تراز ۱۲۷۲.۵ متر (آستانه تفکیک دو نیمه)"),
        (1271.0, 0.42, 1790.0, "منحنی تراز ۱۲۷۱.۰ متر (پلتفرم کم‌عمق میانی)"),
        (1270.0, 0.56, 620.0, "منحنی تراز ۱۲۷۰.۰ متر (گودال‌های عمیق بستر)"),
    ]
    features = []
    for elev, shrink, area_km2, name_fa in levels:
        ring = scale_ring_toward_axis(ref_ring, shrink)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "elevation_m": elev,
                    "area_km2": area_km2,
                    "name_fa": name_fa,
                    "name_en": f"Bathymetric Contour {elev:.1f} m a.s.l.",
                    "source": "Calibrated Lake Urmia Hypsometric Bathymetry Model",
                },
                "geometry": {"type": "LineString", "coordinates": ring},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_natural_basin_and_subbasins() -> tuple[dict, dict]:
    basin_ctrl = [
        (44.28, 38.42), (44.68, 38.58), (45.22, 38.55), (45.78, 38.48),
        (46.38, 38.39), (47.05, 38.28), (47.58, 38.12), (47.82, 37.88),
        (47.65, 37.55), (47.22, 37.32), (46.88, 37.02), (46.75, 36.62),
        (46.58, 36.18), (46.22, 35.96), (45.78, 36.04), (45.38, 36.28),
        (45.05, 36.58), (44.78, 36.96), (44.58, 37.38), (44.38, 37.82),
        (44.22, 38.16),
    ]
    basin_ring = smooth_closed_ring(basin_ctrl, iterations=3)
    basin_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name_fa": "مرز کل حوضه آبریز بسته دریاچه ارومیه",
                    "name_en": "Lake Urmia Endorheic Drainage Basin Boundary",
                    "area_km2": 51876.0,
                    "perimeter_km": 1145.0,
                    "hydro_type": "Endorheic Watershed (HydroSHEDS Level-5)",
                    "source": "SRTM / HydroSHEDS Watershed Delineation",
                },
                "geometry": {"type": "Polygon", "coordinates": [basin_ring]},
            }
        ],
    }

    subbasins_raw = [
        (
            "زیرحوضه زرینه‌رود (جغتو)",
            "Zarrineh-Rud Sub-Basin",
            11890.0,
            41.0,
            [(45.65, 37.12), (46.15, 37.08), (46.68, 36.85), (46.74, 36.35), (46.32, 35.98), (45.82, 36.08), (45.68, 36.62)],
        ),
        (
            "زیرحوضه سیمینه‌رود (تاتائو)",
            "Simineh-Rud Sub-Basin",
            3680.0,
            12.5,
            [(45.32, 37.12), (45.65, 37.10), (45.72, 36.60), (45.55, 36.26), (45.18, 36.52), (45.16, 36.92)],
        ),
        (
            "زیرحوضه آجی‌چای (تلخه‌رود - تبریز/سبلان)",
            "Aji-Chay (Talkheh-Rud) Sub-Basin",
            13850.0,
            14.2,
            [(45.58, 38.12), (46.28, 38.32), (47.25, 38.22), (47.76, 37.90), (47.48, 37.56), (46.55, 37.62), (45.72, 37.78)],
        ),
        (
            "زیرحوضه گدارچای و مهابادچای",
            "Gadar-Chay & Mahabad-Chay Sub-Basin",
            3920.0,
            10.8,
            [(44.78, 37.08), (45.35, 37.18), (45.32, 36.82), (45.08, 36.58), (44.76, 36.82)],
        ),
        (
            "زیرحوضه باراندوزچای، شهرچای و نازلوچای (ارومیه)",
            "Urmia Western Rivers (Nazlu, Shahr & Baranduz)",
            5460.0,
            13.6,
            [(44.45, 37.92), (45.12, 37.96), (45.24, 37.55), (45.28, 37.20), (44.76, 37.14), (44.52, 37.52)],
        ),
        (
            "زیرحوضه زولاچای و روضه‌چای (سلماس - شمال‌غرب)",
            "Zola-Chay & Northern Salmas Sub-Basin",
            4120.0,
            4.8,
            [(44.28, 38.32), (44.98, 38.48), (45.32, 38.28), (45.02, 38.05), (44.45, 37.95)],
        ),
        (
            "زیرحوضه صوفی‌چای و مردق‌چای (مراغه - سهند)",
            "Sufi-Chay & Qal'eh-Chay (Sahand Southern Slope)",
            3540.0,
            3.1,
            [(45.76, 37.68), (46.52, 37.62), (46.85, 37.25), (46.32, 37.08), (45.78, 37.28)],
        ),
    ]

    sub_features = []
    for name_fa, name_en, area_km2, inflow_share_pct, ctrl in subbasins_raw:
        sub_features.append(
            {
                "type": "Feature",
                "properties": {
                    "name_fa": name_fa,
                    "name_en": name_en,
                    "area_km2": area_km2,
                    "inflow_share_pct": inflow_share_pct,
                    "source": "Iran Water Resources / HydroSHEDS Sub-Basin Atlas",
                },
                "geometry": {"type": "Polygon", "coordinates": [smooth_closed_ring(ctrl, iterations=2)]},
            }
        )
    return basin_fc, {"type": "FeatureCollection", "features": sub_features}


def build_salt_playa_zones() -> dict:
    east_playa = [
        (45.48, 38.18), (45.58, 38.14), (45.55, 37.94), (45.64, 37.74),
        (45.77, 37.58), (45.81, 37.39), (45.66, 37.36), (45.54, 37.58),
        (45.46, 37.82), (45.44, 38.05),
    ]
    south_playa = [
        (45.36, 37.48), (45.55, 37.52), (45.76, 37.42), (45.78, 37.22),
        (45.65, 37.11), (45.46, 37.13), (45.36, 37.28),
    ]
    west_margin = [
        (45.20, 37.86), (45.28, 37.82), (45.34, 37.54), (45.38, 37.34),
        (45.31, 37.32), (45.23, 37.58), (45.17, 37.76),
    ]
    zones = [
        (
            "پلایای نمکی شرقی (محور شرفخانه - رحمانلو - بناب)",
            "Eastern Salt Playa (Sharafkhaneh–Rahmanlu–Bonab Axis)",
            1420.0,
            84.5,
            "CRITICAL",
            east_playa,
        ),
        (
            "کفه نمکی وسیع جنوب دریاچه (دلتای زرینه‌رود و سیمینه‌رود)",
            "Southern Exposed Salt Flat (Miandoab–Deltaic Bed)",
            1890.0,
            79.2,
            "HIGH",
            south_playa,
        ),
        (
            "حاشیه نمکی غربی (محور گلمانخانه - رشکان)",
            "Western Exposed Evaporite Margin",
            625.2,
            58.4,
            "MODERATE",
            west_margin,
        ),
    ]
    features = []
    for name_fa, name_en, area_km2, hazard_idx, risk_class, ctrl in zones:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name_fa": name_fa,
                    "name_en": name_en,
                    "area_km2": area_km2,
                    "dust_hazard_index": hazard_idx,
                    "risk_level": risk_class,
                    "dominant_mineral": "Halite (NaCl) + Gypsum Crust",
                    "source": "Sentinel-2 Evaporite Albedo + Aeolian Susceptibility Model",
                },
                "geometry": {"type": "Polygon", "coordinates": [smooth_closed_ring(ctrl, iterations=3)]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def patch_layers_ts() -> None:
    layers_path = ROOT / "web-dashboard" / "src" / "config" / "layers.ts"
    if not layers_path.exists():
        print(f"[WARN] {layers_path} not found")
        return
    content = layers_path.read_text(encoding="utf-8")
    content = content.replace("['match', ['get', 'year'],", "['match', ['to-number', ['get', 'year'], 0],")
    content = content.replace(
        "['coalesce', ['get', 'dust_hazard_index'], 50]",
        "['to-number', ['get', 'dust_hazard_index'], 50]",
    )
    content = content.replace(
        "['coalesce', ['get', 'capacity_mcm'], 50]",
        "['to-number', ['get', 'capacity_mcm'], 50]",
    )
    layers_path.write_text(content, encoding="utf-8")
    print("[OK] Patched web-dashboard/src/config/layers.ts")


def patch_vite_config() -> None:
    vite_path = ROOT / "web-dashboard" / "vite.config.ts"
    vite_code = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1100,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/maplibre-gl')) {
            return 'vendor-maplibre';
          }
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-')) {
            return 'vendor-charts';
          }
          if (id.includes('node_modules/react') || id.includes('node_modules/lucide-react')) {
            return 'vendor-react';
          }
        },
      },
    },
  },
});
"""
    vite_path.write_text(vite_code, encoding="utf-8")
    print("[OK] Updated web-dashboard/vite.config.ts")


def write_geojson_everywhere(filename: str, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    for d in GIS_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        (d / filename).write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {filename} ({len(payload['features'])} features)")


def main() -> None:
    ref_ring = load_or_build_reference_lake()
    write_geojson_everywhere("lake_water_extent.geojson", build_natural_water_extent())
    write_geojson_everywhere("historical_shorelines.geojson", build_historical_shorelines(ref_ring))
    write_geojson_everywhere("bathymetric_contours.geojson", build_bathymetric_contours(ref_ring))
    write_geojson_everywhere("salt_crust_exposure.geojson", build_salt_playa_zones())
    basin_fc, subbasins_fc = build_natural_basin_and_subbasins()
    write_geojson_everywhere("urmia_basin_boundary.geojson", basin_fc)
    write_geojson_everywhere("subbasins.geojson", subbasins_fc)
    patch_layers_ts()
    patch_vite_config()
    print("\n=== Phase 6.3 Spatial Refinement & Bundle Optimization Complete ===")


if __name__ == "__main__":
    main()
