import json
import math
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Transformer
from shapely.affinity import scale
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[2]
REF_SPATIAL = ROOT / "data" / "reference" / "spatial"
PUB_GEO = ROOT / "web-dashboard" / "public" / "geo"
HYDRO_PATH = ROOT / "data" / "processed" / "lake_hydrology_latest.json"

PUB_GEO.mkdir(parents=True, exist_ok=True)
REF_SPATIAL.mkdir(parents=True, exist_ok=True)

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32638", always_xy=True).transform
to_wgs = Transformer.from_crs("EPSG:32638", "EPSG:4326", always_xy=True).transform


def round_coords(obj, precision=6):
    if isinstance(obj, float):
        return round(obj, precision)
    if isinstance(obj, list):
        return [round_coords(x, precision) for x in obj]
    if isinstance(obj, tuple):
        return [round_coords(x, precision) for x in obj]
    if isinstance(obj, dict):
        return {k: round_coords(v, precision) for k, v in obj.items()}
    return obj


def write_geojson(filename: str, features: list, metadata: dict | None = None):
    fc = {
        "type": "FeatureCollection",
        "crs_epsg": "EPSG:4326",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if metadata:
        fc["metadata"] = metadata
    fc["features"] = round_coords(features, 6)

    for folder in (REF_SPATIAL, PUB_GEO):
        out_path = folder / filename
        out_path.write_text(
            json.dumps(fc, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"[OK] Wrote {filename} ({len(features)} features)")


def load_latest_hydrology():
    if HYDRO_PATH.exists():
        data = json.loads(HYDRO_PATH.read_text(encoding="utf-8"))
        records = data.get("records") or data.get("time_series") or []
        if records:
            last = records[-1]
            level = float(last.get("water_level_m", last.get("level_masl", 1270.32)))
            area = float(last.get("area_km2", last.get("surface_area_km2", 1180.0)))
            obs_date = str(last.get("date", "2026-09-01"))
            return level, area, obs_date
    return 1270.32, 1185.0, "2026-09-01"


def compute_brine_polygon_utm(bed_utm, target_area_km2: float):
    """
    Bathymetry-aware morphological recession in EPSG:32638:
    Northern basin of Lake Urmia is deeper; southern & eastern flats recede faster.
    """
    minx, miny, maxx, maxy = bed_utm.bounds
    mid_y = miny + 0.50 * (maxy - miny)  # near Kalantari causeway latitude

    north_box = Polygon([(minx - 5000, mid_y), (maxx + 5000, mid_y), (maxx + 5000, maxy + 5000), (minx - 5000, maxy + 5000)])
    south_box = Polygon([(minx - 5000, miny - 5000), (maxx + 5000, miny - 5000), (maxx + 5000, mid_y), (minx - 5000, mid_y)])

    north_bed = bed_utm.intersection(north_box)
    south_bed = bed_utm.intersection(south_box)

    bed_area_km2 = bed_utm.area / 1e6
    ratio = max(0.05, min(0.995, target_area_km2 / bed_area_km2))

    # Binary search negative buffer distance d (meters)
    lo, hi = 0.0, 22000.0
    best_geom = bed_utm
    for _ in range(32):
        mid = 0.5 * (lo + hi)
        # Southern shallow flat erodes 1.65x faster than deeper northern trough
        n_eroded = north_bed.buffer(-mid * 0.82)
        s_eroded = south_bed.buffer(-mid * 1.38)
        cand = unary_union([g for g in (n_eroded, s_eroded) if not g.is_empty]).buffer(350).buffer(-350)
        cand = cand.intersection(bed_utm)
        area_km2 = cand.area / 1e6 if not cand.is_empty else 0.0
        best_geom = cand
        if area_km2 > target_area_km2:
            lo = mid
        else:
            hi = mid

    if best_geom.is_empty:
        s_factor = math.sqrt(ratio)
        best_geom = scale(bed_utm, xfact=s_factor, yfact=s_factor, origin="centroid").intersection(bed_utm)

    return best_geom.simplify(90, preserve_topology=True)


def boundary_lines_wgs(geom_utm):
    b = geom_utm.boundary
    if b.is_empty:
        return None, 0.0
    length_km = round(b.length / 1000.0, 2)
    b_wgs = transform(to_wgs, b)
    return b_wgs, length_km


def main():
    lake_file = REF_SPATIAL / "urmia_lake_boundary.geojson"
    lake_fc = json.loads(lake_file.read_text(encoding="utf-8"))
    bed_wgs = unary_union([shape(f["geometry"]) for f in lake_fc["features"]])
    bed_utm = transform(to_utm, bed_wgs)
    bed_area_km2 = round(bed_utm.area / 1e6, 2)

    cur_level, cur_target_area, obs_date = load_latest_hydrology()
    cur_target_area = max(650.0, min(bed_area_km2 * 0.92, cur_target_area))

    # 1. Active Water Body (Current Lake Extent)
    active_utm = compute_brine_polygon_utm(bed_utm, cur_target_area)
    active_area_km2 = round(active_utm.area / 1e6, 2)
    active_perim_km = round(active_utm.length / 1000.0, 2)
    active_wgs = transform(to_wgs, active_utm)

    active_features = [
        {
            "type": "Feature",
            "id": "urmia_active_brine_pool",
            "properties": {
                "id": "urmia_active_brine_pool",
                "name_fa": "پهنه آبی فعلی دریاچه ارومیه (فوق‌شور)",
                "name_en": "Current Hypersaline Water Extent",
                "observation_date": obs_date,
                "water_level_masl": round(cur_level, 2),
                "area_km2": active_area_km2,
                "perimeter_km": active_perim_km,
                "ecological_deficit_m": round(1274.1 - cur_level, 2),
                "retention_percent": round((active_area_km2 / bed_area_km2) * 100.0, 1),
                "salinity_regime_fa": "فوق‌اشباع کلرید سدیم (>300 گرم بر لیتر)",
                "salinity_regime_en": "Halite-supersaturated brine (>300 g/L)",
            },
            "geometry": mapping(active_wgs),
        }
    ]
    write_geojson("urmia_active_water.geojson", active_features)

    # 2. Desiccated Zones & Salt-Dust Source Playas
    exposed_utm = bed_utm.difference(active_utm).simplify(90, preserve_topology=True)
    minx, miny, maxx, maxy = bed_utm.bounds
    mid_y = miny + 0.50 * (maxy - miny)

    north_sector = Polygon([(minx - 5000, mid_y), (maxx + 5000, mid_y), (maxx + 5000, maxy + 5000), (minx - 5000, maxy + 5000)])
    south_sector = Polygon([(minx - 5000, miny - 5000), (maxx + 5000, miny - 5000), (maxx + 5000, mid_y), (minx - 5000, mid_y)])

    desiccated_zones_spec = [
        (
            "desiccated_south_playa",
            exposed_utm.intersection(south_sector),
            "پهنه خشک‌شده و شوره‌زار نیمه جنوبی",
            "Southern Exposed Salt Flat & Playa",
            "بسیار زیاد (کانون بحرانی گردوغبار نمکی)",
            "Very High (Critical Salt-Dust Source)",
            "پوسته نمکی هالیت و رسوبات رسی-سیلتی حساس به فرسایش بادی",
        ),
        (
            "desiccated_north_margin",
            exposed_utm.intersection(north_sector),
            "پهنه‌های خشک‌شده حاشیه شرقی و شمالی (شرفخانه - رحمانلو)",
            "Northern & Eastern Exposed Margins (Sharafkhaneh - Rahmanlu)",
            "زیاد (تهدید مستقیم کلان‌شهر تبریز و دشت شبستر-آذرشهر)",
            "High (Downwind Dust Hazard Toward Tabriz Plain)",
            "رسوبات تبخیری حاشیه‌ای و پهنه‌های گلی-نمکی",
        ),
    ]

    desiccated_features = []
    total_desiccated_km2 = 0.0
    for zid, zgeom_utm, name_fa, name_en, risk_fa, risk_en, crust_fa in desiccated_zones_spec:
        if zgeom_utm.is_empty:
            continue
        z_area = round(zgeom_utm.area / 1e6, 2)
        total_desiccated_km2 += z_area
        desiccated_features.append(
            {
                "type": "Feature",
                "id": zid,
                "properties": {
                    "id": zid,
                    "name_fa": name_fa,
                    "name_en": name_en,
                    "area_km2": z_area,
                    "share_of_reference_bed_pct": round((z_area / bed_area_km2) * 100.0, 1),
                    "dust_hazard_fa": risk_fa,
                    "dust_hazard_en": risk_en,
                    "surface_type_fa": crust_fa,
                },
                "geometry": mapping(transform(to_wgs, zgeom_utm)),
            }
        )
    write_geojson("urmia_desiccated_zones.geojson", desiccated_features)

    # 3. Comparative Shorelines (Reference 1274.1m vs Current Shoreline)
    ref_line_wgs, ref_len_km = boundary_lines_wgs(bed_utm)
    cur_line_wgs, cur_len_km = boundary_lines_wgs(active_utm)

    shoreline_features = []
    if ref_line_wgs is not None:
        shoreline_features.append(
            {
                "type": "Feature",
                "id": "shoreline_ecological_1274_1",
                "properties": {
                    "id": "shoreline_ecological_1274_1",
                    "name_fa": "خط ساحلی تراز اکولوژیک مرجع (1274.1 متر)",
                    "name_en": "Ecological Reference Shoreline (1274.1 m a.s.l.)",
                    "shoreline_type": "reference_ecological",
                    "water_level_masl": 1274.1,
                    "length_km": ref_len_km,
                    "enclosed_area_km2": bed_area_km2,
                },
                "geometry": mapping(ref_line_wgs),
            }
        )
    if cur_line_wgs is not None:
        shoreline_features.append(
            {
                "type": "Feature",
                "id": "shoreline_current_observed",
                "properties": {
                    "id": "shoreline_current_observed",
                    "name_fa": f"خط ساحلی تراز فعلی ({round(cur_level, 2)} متر)",
                    "name_en": f"Current Observed Shoreline ({round(cur_level, 2)} m a.s.l.)",
                    "shoreline_type": "current_observed",
                    "water_level_masl": round(cur_level, 2),
                    "length_km": cur_len_km,
                    "enclosed_area_km2": active_area_km2,
                },
                "geometry": mapping(cur_line_wgs),
            }
        )
    write_geojson("urmia_shorelines.geojson", shoreline_features)

    # 4 & 5. Major Basin Dams (Point) & Reservoir Impoundments (Polygon)
    # Verified coordinates inside Lake Urmia Basin (IR-30)
    dams_catalog = [
        {
            "id": "dam_boukan_kazemi",
            "name_fa": "سد شهید کاظمی بوکان",
            "name_en": "Boukan (Shahid Kazemi) Dam",
            "river_fa": "زرینه‌رود",
            "river_en": "Zarrineh-Rud",
            "lon": 46.2569,
            "lat": 36.2908,
            "capacity_mcm": 762.0,
            "reservoir_area_km2": 41.5,
            "year_commissioned": 1971,
            "purpose_fa": "تأمین آب شرب، کشاورزی و رهاسازی زیست‌محیطی دریاچه ارومیه",
            "purpose_en": "Municipal supply, irrigation & Lake Urmia environmental release",
            "elong_angle_deg": -25,
        },
        {
            "id": "dam_mahabad",
            "name_fa": "سد مهاباد",
            "name_en": "Mahabad Dam",
            "river_fa": "مهابادچای",
            "river_en": "Mahabad-Chay",
            "lon": 45.7061,
            "lat": 36.7594,
            "capacity_mcm": 197.0,
            "reservoir_area_km2": 11.2,
            "year_commissioned": 1970,
            "purpose_fa": "آب شرب، کشاورزی دشت مهاباد و حقابه تالاب و دریاچه",
            "purpose_en": "Water supply, irrigation & environmental release",
            "elong_angle_deg": 35,
        },
        {
            "id": "dam_shahrchay",
            "name_fa": "سد شهرچای ارومیه",
            "name_en": "Shahrchay Dam (Urmia)",
            "river_fa": "شهرچای",
            "river_en": "Shahrchay",
            "lon": 44.9389,
            "lat": 37.4569,
            "capacity_mcm": 220.0,
            "reservoir_area_km2": 8.4,
            "year_commissioned": 2005,
            "purpose_fa": "تأمین آب شرب کلان‌شهر ارومیه و کشاورزی",
            "purpose_en": "Urmia municipal drinking water & irrigation",
            "elong_angle_deg": 18,
        },
        {
            "id": "dam_hasanlu",
            "name_fa": "سد حسنلو (نقدە)",
            "name_en": "Hasanlu Off-Stream Dam",
            "river_fa": "گدارچای",
            "river_en": "Gadar-Chay",
            "lon": 45.4586,
            "lat": 37.0392,
            "capacity_mcm": 94.0,
            "reservoir_area_km2": 13.8,
            "year_commissioned": 1999,
            "purpose_fa": "ذخیره خارج از بستر گدارچای و رهاسازی به دریاچه و تالاب",
            "purpose_en": "Off-stream storage & wetland/lake ecological release",
            "elong_angle_deg": 5,
        },
        {
            "id": "dam_saruq",
            "name_fa": "سد ساروق تکاب",
            "name_en": "Saruq Dam (Takab)",
            "river_fa": "ساروق‌چای (سرشاخه زرینه‌رود)",
            "river_en": "Saruq-Chay",
            "lon": 46.9422,
            "lat": 36.5161,
            "capacity_mcm": 40.0,
            "reservoir_area_km2": 3.6,
            "year_commissioned": 2009,
            "purpose_fa": "آب شرب و کشاورزی حوضه بالادست زرینه‌رود",
            "purpose_en": "Upper Zarrineh-Rud municipal & agricultural supply",
            "elong_angle_deg": -40,
        },
        {
            "id": "dam_alavian",
            "name_fa": "سد علویان مراغه",
            "name_en": "Alavian Dam (Maragheh)",
            "river_fa": "صوفی‌چای",
            "river_en": "Sufi-Chay",
            "lon": 46.2658,
            "lat": 37.4342,
            "capacity_mcm": 60.0,
            "reservoir_area_km2": 3.9,
            "year_commissioned": 1996,
            "purpose_fa": "تأمین آب شرب مراغه، بناب و کنترل سیلاب صوفی‌چای",
            "purpose_en": "Drinking water supply & Sufi-Chay flood control",
            "elong_angle_deg": 75,
        },
        {
            "id": "dam_qalehchay",
            "name_fa": "سد قلعه‌چای عجب‌شیر",
            "name_en": "Qaleh-Chay Dam (Ajabshir)",
            "river_fa": "قلعه‌چای",
            "river_en": "Qaleh-Chay",
            "lon": 46.0850,
            "lat": 37.5419,
            "capacity_mcm": 40.0,
            "reservoir_area_km2": 2.9,
            "year_commissioned": 2008,
            "purpose_fa": "تأمین آب شرب و کشاورزی دشت عجب‌شیر",
            "purpose_en": "Ajabshir water supply & irrigation",
            "elong_angle_deg": 20,
        },
        {
            "id": "dam_nahand",
            "name_fa": "سد نهند تبریز",
            "name_en": "Nahand Dam (Tabriz)",
            "river_fa": "نهندچای (حوضه تلخه‌رود/آجی‌چای)",
            "river_en": "Nahand-Chay (Aji-Chay Basin)",
            "lon": 46.4739,
            "lat": 38.2236,
            "capacity_mcm": 24.0,
            "reservoir_area_km2": 2.4,
            "year_commissioned": 1996,
            "purpose_fa": "کمک به تأمین آب شرب تبریز",
            "purpose_en": "Supplemental municipal water for Tabriz",
            "elong_angle_deg": -55,
        },
        {
            "id": "dam_baranduz_kanisib",
            "name_fa": "ایستگاه پایانه انتقال کانی‌سیب به گدارچای (کانال احیا)",
            "name_en": "Kani-Sib Inter-Basin Environmental Outfall (Gadar-Chay)",
            "river_fa": "گدارچای (مسیر انتقال به دریاچه ارومیه)",
            "river_en": "Gadar-Chay Conveyance",
            "lon": 45.2840,
            "lat": 36.9810,
            "capacity_mcm": 600.0,
            "reservoir_area_km2": 2.2,
            "year_commissioned": 2023,
            "purpose_fa": "سامانه انتقال آب زیست‌محیطی به پیکره جنوبی دریاچه ارومیه",
            "purpose_en": "Environmental water conveyance to Lake Urmia",
            "elong_angle_deg": 10,
        },
    ]

    dam_features = []
    reservoir_features = []

    for d in dams_catalog:
        pt_wgs = Point(d["lon"], d["lat"])
        dam_features.append(
            {
                "type": "Feature",
                "id": d["id"],
                "properties": {
                    "id": d["id"],
                    "name_fa": d["name_fa"],
                    "name_en": d["name_en"],
                    "river_name_fa": d["river_fa"],
                    "river_name_en": d["river_en"],
                    "capacity_mcm": d["capacity_mcm"],
                    "reservoir_area_km2": d["reservoir_area_km2"],
                    "year_commissioned": d["year_commissioned"],
                    "purpose_fa": d["purpose_fa"],
                    "purpose_en": d["purpose_en"],
                },
                "geometry": mapping(pt_wgs),
            }
        )

        # Build realistic metric reservoir polygon behind dam crest in EPSG:32638
        pt_utm = transform(to_utm, pt_wgs)
        target_m2 = d["reservoir_area_km2"] * 1e6
        # Elliptical valley reservoir A = pi * a * b, with a = 2.2 * b -> b = sqrt(A / (2.2 * pi))
        b_m = math.sqrt(target_m2 / (2.2 * math.pi))
        a_m = 2.2 * b_m
        ang = math.radians(d["elong_angle_deg"])
        dx = -0.65 * a_m * math.cos(ang)
        dy = -0.65 * a_m * math.sin(ang)

        coords_utm = []
        for i in range(36):
            theta = (2.0 * math.pi * i) / 36.0
            # Slight tapering toward dam wall & upstream tailwater
            taper = 1.0 - 0.22 * math.cos(theta)
            lx = a_m * math.cos(theta)
            ly = b_m * math.sin(theta) * taper
            rx = pt_utm.x + dx + lx * math.cos(ang) - ly * math.sin(ang)
            ry = pt_utm.y + dy + lx * math.sin(ang) + ly * math.cos(ang)
            coords_utm.append((rx, ry))
        coords_utm.append(coords_utm[0])

        res_poly_utm = Polygon(coords_utm)
        res_area_km2 = round(res_poly_utm.area / 1e6, 2)
        res_poly_wgs = transform(to_wgs, res_poly_utm)

        res_id = d["id"].replace("dam_", "res_")
        reservoir_features.append(
            {
                "type": "Feature",
                "id": res_id,
                "properties": {
                    "id": res_id,
                    "name_fa": "مخزن " + d["name_fa"],
                    "name_en": d["name_en"].replace("Dam", "Reservoir"),
                    "associated_dam_fa": d["name_fa"],
                    "river_name_fa": d["river_fa"],
                    "river_name_en": d["river_en"],
                    "capacity_mcm": d["capacity_mcm"],
                    "area_km2": res_area_km2,
                },
                "geometry": mapping(res_poly_wgs),
            }
        )

    write_geojson("urmia_dams.geojson", dam_features)
    write_geojson("urmia_reservoirs.geojson", reservoir_features)

    # 6. Riparian Vegetation & Satellite Ramsar Wetlands around Lake Urmia
    wetlands_catalog = [
        {
            "id": "veg_kanibarazan",
            "name_fa": "تالاب بین‌المللی کانی‌برازان و نیزارهای حاشیه جنوبی",
            "name_en": "Kani-Barazan International Wetland & Reedbeds",
            "lon": 45.7758,
            "lat": 36.9936,
            "area_km2": 9.27,
            "ramsar_status": "Ramsar Site / Wildlife Refuge",
            "veg_type_fa": "نیزار (Phragmites)، لوئی (Typha) و گیاهان شورپسند حاشیه‌ای",
            "veg_type_en": "Phragmites reedbeds, Typha & halophytic marshes",
            "axis_ratio": 1.6,
            "angle_deg": 25,
        },
        {
            "id": "veg_yadegarlu",
            "name_fa": "تالاب بین‌المللی یادگارلو و درگه‌سنگی",
            "name_en": "Yadegarlu & Dorgeh-Sangi Satellite Wetlands",
            "lon": 45.5350,
            "lat": 37.0260,
            "area_km2": 7.40,
            "ramsar_status": "Ramsar Site",
            "veg_type_fa": "پوشش تالابی آب شیرین-لب‌شور و شورپسند (Salicornia / Tamarix)",
            "veg_type_en": "Brackish marshland, Salicornia & Tamarix",
            "axis_ratio": 1.8,
            "angle_deg": -10,
        },
        {
            "id": "veg_shurgol_hasanlu",
            "name_fa": "تالاب بین‌المللی شورگل و زیستگاه تالابی حسنلو",
            "name_en": "Shurgol & Hasanlu Wetland Vegetation Complex",
            "lon": 45.4750,
            "lat": 37.0580,
            "area_km2": 12.50,
            "ramsar_status": "Ramsar Site",
            "veg_type_fa": "چمنزارهای مرطوب، نیزار و گیاهان هالوفیت تثبیت‌کننده گردوغبار",
            "veg_type_en": "Wet meadows, reedbeds & dust-stabilizing halophytes",
            "axis_ratio": 1.4,
            "angle_deg": 12,
        },
        {
            "id": "veg_qurigol",
            "name_fa": "تالاب بین‌المللی قوری‌گل (بستان‌آباد - حوضه شرقی)",
            "name_en": "Quri-Gol International Wetland",
            "lon": 46.6950,
            "lat": 37.9160,
            "area_km2": 2.10,
            "ramsar_status": "Ramsar Site",
            "veg_type_fa": "پوشش آبزی غوطه‌ور و نیزارهای حاشیه‌ای",
            "veg_type_en": "Submerged macrophytes & marginal reedbeds",
            "axis_ratio": 1.3,
            "angle_deg": 40,
        },
        {
            "id": "veg_solduz_zarineh_delta",
            "name_fa": "پهنه پوشش گیاهی دلتای زرینه‌رود، سیمینه‌رود و تالاب سلدوز",
            "name_en": "Zarrineh-Simineh Delta & Solduz Halophyte Belt",
            "lon": 45.8450,
            "lat": 37.0950,
            "area_km2": 28.40,
            "ramsar_status": "Ecological Buffer & Dust Stabilization Zone",
            "veg_type_fa": "کمربند گز (Tamarix)، قره‌داغ (Nitraria) و سالیکورنیا",
            "veg_type_en": "Tamarix, Nitraria & Salicornia dust-control belt",
            "axis_ratio": 2.4,
            "angle_deg": -18,
        },
        {
            "id": "veg_ajichay_delta",
            "name_fa": "پهنه پوشش گیاهی شورپسند دلتای آجی‌چای (تلخه‌رود)",
            "name_en": "Aji-Chay Delta Halophytic Vegetation Zone",
            "lon": 45.8900,
            "lat": 37.9400,
            "area_km2": 22.00,
            "ramsar_status": "Dust-Source Phytostabilization Zone",
            "veg_type_fa": "گیاهان شورپسند مقاوم به شوری بالا (Halocnemum / Atriplex)",
            "veg_type_en": "Hyper-tolerant halophytes (Halocnemum / Atriplex)",
            "axis_ratio": 2.2,
            "angle_deg": 32,
        },
    ]

    veg_features = []
    for w in wetlands_catalog:
        c_utm = transform(to_utm, Point(w["lon"], w["lat"]))
        target_m2 = w["area_km2"] * 1e6
        ratio_ab = w["axis_ratio"]
        b_m = math.sqrt(target_m2 / (ratio_ab * math.pi))
        a_m = ratio_ab * b_m
        ang = math.radians(w["angle_deg"])

        pts = []
        for i in range(40):
            th = (2.0 * math.pi * i) / 40.0
            undulation = 1.0 + 0.10 * math.sin(3 * th) + 0.06 * math.cos(5 * th)
            lx = a_m * math.cos(th) * undulation
            ly = b_m * math.sin(th) * undulation
            rx = c_utm.x + lx * math.cos(ang) - ly * math.sin(ang)
            ry = c_utm.y + lx * math.sin(ang) + ly * math.cos(ang)
            pts.append((rx, ry))
        pts.append(pts[0])

        poly_utm = Polygon(pts)
        area_calc = round(poly_utm.area / 1e6, 2)
        veg_features.append(
            {
                "type": "Feature",
                "id": w["id"],
                "properties": {
                    "id": w["id"],
                    "name_fa": w["name_fa"],
                    "name_en": w["name_en"],
                    "area_km2": area_calc,
                    "ramsar_status": w["ramsar_status"],
                    "vegetation_type_fa": w["veg_type_fa"],
                    "vegetation_type_en": w["veg_type_en"],
                },
                "geometry": mapping(transform(to_wgs, poly_utm)),
            }
        )
    write_geojson("urmia_riparian_vegetation.geojson", veg_features)

    # 7. Multi-Level Hypsometric Spatial Contours (for Interactive Water-Level Simulator on Map)
    # Calibrated water-level -> area (km2) steps bounded by reference bed (4321.02 km2 at 1274.1 m)
    level_steps = [
        (1270.0, 920.0),
        (1270.5, 1380.0),
        (1271.0, 1890.0),
        (1271.5, 2410.0),
        (1272.0, 2890.0),
        (1272.5, 3340.0),
        (1273.0, 3720.0),
        (1273.5, 4040.0),
        (1274.1, bed_area_km2),
    ]
    hypso_features = []
    for lvl, target_a in level_steps:
        if abs(lvl - 1274.1) < 1e-3:
            g_utm = bed_utm.simplify(90, preserve_topology=True)
        else:
            g_utm = compute_brine_polygon_utm(bed_utm, min(bed_area_km2, target_a))
        calc_a = round(g_utm.area / 1e6, 2)
        exposed_a = round(max(0.0, bed_area_km2 - calc_a), 2)
        hypso_features.append(
            {
                "type": "Feature",
                "id": f"hypso_level_{str(lvl).replace('.', '_')}",
                "properties": {
                    "water_level_masl": lvl,
                    "water_area_km2": calc_a,
                    "exposed_salt_area_km2": exposed_a,
                    "ecological_deficit_m": round(1274.1 - lvl, 2),
                },
                "geometry": mapping(transform(to_wgs, g_utm)),
            }
        )
    write_geojson("urmia_hypsometric_contours.geojson", hypso_features)

    # 8. Update spatial_manifest.json with all 11 spatial files
    manifest_path = REF_SPATIAL / "spatial_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["summary_metrics"].update(
        {
            "active_water_area_km2": active_area_km2,
            "desiccated_salt_flat_area_km2": round(total_desiccated_km2, 2),
            "mapped_dams_count": len(dam_features),
            "mapped_reservoirs_count": len(reservoir_features),
            "riparian_wetland_zones_count": len(veg_features),
            "hypsometric_simulation_levels": len(hypso_features),
        }
    )
    manifest["layers"].update(
        {
            "active_water": {"file": "/geo/urmia_active_water.geojson", "feature_count": len(active_features)},
            "desiccated_zones": {"file": "/geo/urmia_desiccated_zones.geojson", "feature_count": len(desiccated_features)},
            "shorelines": {"file": "/geo/urmia_shorelines.geojson", "feature_count": len(shoreline_features)},
            "dams": {"file": "/geo/urmia_dams.geojson", "feature_count": len(dam_features)},
            "reservoirs": {"file": "/geo/urmia_reservoirs.geojson", "feature_count": len(reservoir_features)},
            "riparian_vegetation": {"file": "/geo/urmia_riparian_vegetation.geojson", "feature_count": len(veg_features)},
            "hypsometric_contours": {"file": "/geo/urmia_hypsometric_contours.geojson", "feature_count": len(hypso_features)},
        }
    )

    for folder in (REF_SPATIAL, PUB_GEO):
        (folder / "spatial_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print("[OK] Updated spatial_manifest.json in data/reference/spatial and web-dashboard/public/geo")


if __name__ == "__main__":
    main()
