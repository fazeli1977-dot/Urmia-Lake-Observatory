"""Reference hydrological features for Lake Urmia closed basin (endorheic watershed, sub-basins, and monitoring landmarks)."""

from typing import Dict, Any, List, Tuple
from shapely.geometry import Polygon, Point, box, mapping

from src.geospatial.crs_utils import (
    compute_area_perimeter_km,
    ensure_valid_geometry,
)

# Calibrated closed watershed divide of Lake Urmia (Endorheic Basin ~51,710 km2 in EPSG:32638)
# Follows real topographic divides: Zagros/Kurdistan border mountains (W), Mishow-Moro (N),
# Sabalan-Bozqush-Sahand divide near Sarab (E), and Zarrineh-Simineh headwaters near Saqqez/Takab (S).
WATERSHED_RING_LONLAT: List[Tuple[float, float]] = [
    (44.280000, 38.280000),
    (44.820000, 38.420000),
    (45.450000, 38.400000),
    (46.080000, 38.280000),
    (46.750000, 38.180000),
    (47.420000, 38.050000),
    (47.550000, 37.720000),
    (47.020000, 37.420000),
    (46.680000, 37.020000),
    (47.100000, 36.620000),
    (47.220000, 36.250000),
    (46.720000, 36.080000),
    (46.220000, 36.050000),
    (45.680000, 36.080000),
    (45.280000, 36.450000),
    (44.820000, 36.880000),
    (44.520000, 37.380000),
    (44.320000, 37.850000),
    (44.280000, 38.280000),
]


def _watershed_polygon() -> Polygon:
    poly = ensure_valid_geometry(Polygon(WATERSHED_RING_LONLAT))
    return poly


def build_watershed_geojson() -> Dict[str, Any]:
    """Return GeoJSON FeatureCollection for the Lake Urmia closed watershed basin."""
    poly = _watershed_polygon()
    area_km2, perimeter_km = compute_area_perimeter_km(poly)

    return {
        "type": "FeatureCollection",
        "name": "urmia_watershed_basin",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": "urmia_endorheic_basin",
                    "name_fa": "حوضه آبریز بسته دریاچه ارومیه",
                    "name_en": "Lake Urmia Endorheic Watershed Basin",
                    "basin_code": "IR-30",
                    "hydrology_type": "endorheic_closed_basin",
                    "area_km2": area_km2,
                    "perimeter_km": perimeter_km,
                    "provinces_fa": "آذربایجان غربی، آذربایجان شرقی، کردستان",
                },
                "geometry": mapping(poly),
            }
        ],
    }


def build_subbasins_geojson() -> Dict[str, Any]:
    """Partition the watershed into the 4 canonical hydrological sub-basin sectors."""
    basin = _watershed_polygon()

    sectors = [
        {
            "id": "subbasin_south",
            "name_fa": "زیرحوضه جنوبی (زرینه‌رود، سیمینه‌رود و مهابادچای)",
            "name_en": "Southern Sub-basin (Zarrineh, Simineh & Mahabad Rivers)",
            "inflow_share_pct": 65.0,
            "dominant_rivers_fa": "زرینه‌رود، سیمینه‌رود، مهابادچای، گدارچای",
            "clip_box": box(44.0, 35.5, 48.0, 37.12),
        },
        {
            "id": "subbasin_east",
            "name_fa": "زیرحوضه شرقی (تلخه‌رود / آجی‌چای و صوفی‌چای)",
            "name_en": "Eastern Sub-basin (Aji Chay & Sufi Chay)",
            "inflow_share_pct": 14.0,
            "dominant_rivers_fa": "تلخه‌رود (آجی‌چای)، صوفی‌چای، مردق‌چای، قلعه‌چای",
            "clip_box": box(45.55, 37.12, 48.0, 38.6),
        },
        {
            "id": "subbasin_west",
            "name_fa": "زیرحوضه غربی (شهرچای، باراندوزچای، نازلوچای و روضه‌چای)",
            "name_en": "Western Sub-basin (Shahr, Baranduz & Nazlu Rivers)",
            "inflow_share_pct": 17.0,
            "dominant_rivers_fa": "باراندوزچای، شهرچای، نازلوچای، روضه‌چای",
            "clip_box": box(44.0, 37.12, 45.55, 38.12),
        },
        {
            "id": "subbasin_north",
            "name_fa": "زیرحوضه شمالی (زولاچای و شبستر-طسوج)",
            "name_en": "Northern Sub-basin (Zola Chay & Northern Flank)",
            "inflow_share_pct": 4.0,
            "dominant_rivers_fa": "زولاچای، دره‌رودهای میشو",
            "clip_box": box(44.0, 38.12, 45.55, 38.6),
        },
    ]

    features = []
    for sec in sectors:
        clipped = ensure_valid_geometry(basin.intersection(sec["clip_box"]))
        area_km2, perimeter_km = compute_area_perimeter_km(clipped)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": sec["id"],
                    "name_fa": sec["name_fa"],
                    "name_en": sec["name_en"],
                    "inflow_share_pct": sec["inflow_share_pct"],
                    "dominant_rivers_fa": sec["dominant_rivers_fa"],
                    "area_km2": area_km2,
                    "perimeter_km": perimeter_km,
                },
                "geometry": mapping(clipped),
            }
        )

    return {
        "type": "FeatureCollection",
        "name": "urmia_subbasins",
        "features": features,
    }


def build_landmarks_geojson() -> Dict[str, Any]:
    """Return scientifically verified hydraulic, ecological, and monitoring landmarks."""
    raw_landmarks = [
        {
            "id": "kalantari_causeway_gap",
            "name_fa": "شکاف هیدرولیکی و پل میانگذر شهید کلانتری",
            "name_en": "Shahid Kalantari Causeway Hydraulic Bridge",
            "category": "hydraulic_structure",
            "lon": 45.2856,
            "lat": 37.7914,
            "description_fa": "مرز تبادل هیدرولیکی نیمه شمالی و جنوبی دریاچه؛ گلوگاه کلیدی چرخش آب و گرادیان شوری.",
        },
        {
            "id": "kaboudan_island",
            "name_fa": "جزیره کبودان (قویون‌داغی) - پناهگاه حیات‌وحش",
            "name_en": "Kaboudan Island National Park Core",
            "category": "ecological_island",
            "lon": 45.6250,
            "lat": 37.4750,
            "description_fa": "بزرگ‌ترین جزیره دریاچه ارومیه با چشمه آب شیرین؛ زیستگاه قوچ و میش ارمنی و شاخص اتصال پل زمینی شوره.",
        },
        {
            "id": "ashk_island",
            "name_fa": "جزیره اشک - زیستگاه گوزن زرد ایرانی",
            "name_en": "Ashk Island Ecological Sanctuary",
            "category": "ecological_island",
            "lon": 45.5150,
            "lat": 37.3820,
            "description_fa": "زیستگاه اصلی گوزن زرد ایرانی؛ بسیار حساس به تشکیل پل نمکی با ساحل در ترازهای بحرانی.",
        },
        {
            "id": "espir_island",
            "name_fa": "جزیره اسپیر",
            "name_en": "Espir Island",
            "category": "ecological_island",
            "lon": 45.5680,
            "lat": 37.6050,
            "description_fa": "یکی از جزایر چهارگانه اصلی پارک ملی دریاچه ارومیه در بخش میانی-جنوبی.",
        },
        {
            "id": "golmankhaneh_gauge",
            "name_fa": "ایستگاه ترازسنجی بندر گلمانخانه (ارومیه)",
            "name_en": "Bandar Golmankhaneh Hydrometric Station",
            "category": "hydrometric_station",
            "lon": 45.2492,
            "lat": 37.5994,
            "description_fa": "ایستگاه مرجع پایش تراز سطح آب دریاچه در ساحل غربی.",
        },
        {
            "id": "sharafkhaneh_gauge",
            "name_fa": "ایستگاه ترازسنجی بندر شرفخانه (شمال دریاچه)",
            "name_en": "Bandar Sharafkhaneh Hydrometric Station",
            "category": "hydrometric_station",
            "lon": 45.4839,
            "lat": 38.1725,
            "description_fa": "ایستگاه تاریخی پایش تراز آب در حوضه شمالی دریاچه ارومیه.",
        },
        {
            "id": "zarrineh_estuary",
            "name_fa": "مصب و دلتای زرینه‌رود (تغذیه‌کننده اصلی جنوب)",
            "name_en": "Zarrineh Rud Delta & Inflow Mouth",
            "category": "river_estuary",
            "lon": 45.7350,
            "lat": 37.1350,
            "description_fa": "مهم‌ترین ورودی آب شیرین دریاچه ارومیه (تأمین‌کننده بیش از ۴۰ درصد آورد سطحی سالانه).",
        },
        {
            "id": "aji_chay_delta",
            "name_fa": "پهنه دلتایی تلخه‌رود (آجی‌چای) و کانون گردوغبار شرق",
            "name_en": "Aji Chay Delta & Eastern Salt/Dust Hotspot",
            "category": "dust_hotspot",
            "lon": 45.8200,
            "lat": 37.9200,
            "description_fa": "پهنه کم‌عمق شرقی؛ یکی از حساس‌ترین کانون‌های خیزش ریزگرد نمکی به سمت کلان‌شهر تبریز و آذرشهر.",
        },
        {
            "id": "kanisib_inlet_zone",
            "name_fa": "خروجی سامانه انتقال آب کانی‌سیب به گدارچای / جنوب دریاچه",
            "name_en": "Kani Sib Water Transfer Release Zone",
            "category": "water_transfer",
            "lon": 45.7744,
            "lat": 36.9922,
            "description_fa": "مسیر رهاسازی آب انتقالی جنوب حوضه به سمت پهنه جنوبی دریاچه ارومیه.",
        },
    ]

    features = []
    for item in raw_landmarks:
        pt = Point(item["lon"], item["lat"])
        props = {k: v for k, v in item.items()}
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": mapping(pt),
            }
        )

    return {
        "type": "FeatureCollection",
        "name": "urmia_monitoring_landmarks",
        "features": features,
    }