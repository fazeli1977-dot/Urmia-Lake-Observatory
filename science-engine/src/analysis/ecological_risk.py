from typing import Dict, Any, List
import numpy as np
import pandas as pd


ECOLOGICAL_TARGET_LEVEL_M = 1274.10
ARTEMIA_VIABLE_SALINITY_G_L = 240.0
HALITE_SATURATION_CAP_G_L = 345.0
REFERENCE_DISSOLVED_SALT_MASS_MT = 820.0  # میلیون تن نمک محلول مرجع در شرایط نرمال


def interpolate_hypsometry(curve: List[Dict[str, Any]], target_level_m: float) -> Dict[str, float]:
    """درون‌یابی مساحت و حجم در تراز دلخواه از روی منحنی هپسومتری دریاچه"""
    df = pd.DataFrame(curve)
    lvl_col = next(c for c in ["level_m", "water_level_m", "elevation_m"] if c in df.columns)
    area_col = next(c for c in ["area_km2", "surface_area_km2"] if c in df.columns)
    vol_col = next(c for c in ["volume_km3", "storage_km3"] if c in df.columns)

    df = df.sort_values(lvl_col).reset_index(drop=True)
    levels = df[lvl_col].to_numpy(dtype=float)
    areas = df[area_col].to_numpy(dtype=float)
    vols = df[vol_col].to_numpy(dtype=float)

    interp_area = float(np.interp(target_level_m, levels, areas))
    interp_vol = float(np.interp(target_level_m, levels, vols))
    max_area = float(np.max(areas))

    return {
        "level_m": round(target_level_m, 3),
        "area_km2": round(interp_area, 2),
        "volume_km3": round(interp_vol, 3),
        "max_historical_area_km2": round(max_area, 2),
    }


def compute_salinity_and_artemia_status(volume_km3: float) -> Dict[str, Any]:
    """
    تخمین غلظت شوری (g/L) بر اساس پایستگی جرم نمک با سقف اشباع هالیت (~345 g/L)
    """
    vol_safe = max(float(volume_km3), 0.05)
    # 1 MT / 1 km3 = 1 g/L
    theoretical_salinity = REFERENCE_DISSOLVED_SALT_MASS_MT / vol_safe
    effective_salinity = min(theoretical_salinity, HALITE_SATURATION_CAP_G_L)
    precipitated_fraction = max(0.0, 1.0 - (effective_salinity / theoretical_salinity))

    if effective_salinity <= 180.0:
        artemia_status = "optimal"
    elif effective_salinity <= ARTEMIA_VIABLE_SALINITY_G_L:
        artemia_status = "stressed_viable"
    elif effective_salinity < 300.0:
        artemia_status = "critical_cyst_dormancy"
    else:
        artemia_status = "collapsed_hypersaline_saturation"

    return {
        "estimated_salinity_g_l": round(effective_salinity, 1),
        "halite_supersaturated": bool(theoretical_salinity > HALITE_SATURATION_CAP_G_L),
        "estimated_precipitated_salt_ratio": round(precipitated_fraction, 4),
        "artemia_threshold_g_l": ARTEMIA_VIABLE_SALINITY_G_L,
        "artemia_ecological_status": artemia_status,
    }


def compute_climate_stress(era5_block: Any) -> Dict[str, Any]:
    """تحلیل تنش اقلیمی و خشکی بر اساس داده‌های ERA5 موجود در JSON"""
    records: List[Dict[str, Any]] = []
    if isinstance(era5_block, list):
        records = era5_block
    elif isinstance(era5_block, dict):
        for key in ["monthly_series", "timeseries", "records", "data", "recent_months"]:
            if isinstance(era5_block.get(key), list):
                records = era5_block[key]
                break

    if not records:
        # بررسی فیلدهای خلاصه در صورتی که دیکشنری خلاصه باشد
        if isinstance(era5_block, dict):
            precip = float(era5_block.get("annual_precipitation_mm", era5_block.get("precipitation_mm", 240.0)))
            evap = float(era5_block.get("annual_evaporation_mm", era5_block.get("evaporation_mm", 1150.0)))
            temp = float(era5_block.get("mean_temp_c", era5_block.get("temperature_2m_c", 13.5)))
        else:
            precip, evap, temp = 240.0, 1150.0, 13.5

        aridity_ratio = round(precip / max(evap, 1.0), 4)
        climate_stress_score = float(np.clip((1.0 - min(aridity_ratio / 0.35, 1.0)) * 100.0, 0.0, 100.0))
        return {
            "source_mode": "summary_metrics",
            "annual_equiv_precip_mm": round(precip, 2),
            "annual_equiv_evap_mm": round(evap, 2),
            "mean_temp_c": round(temp, 2),
            "p_to_e_ratio": aridity_ratio,
            "climate_stress_score_0_100": round(climate_stress_score, 1),
        }

    df = pd.DataFrame(records)
    p_col = next((c for c in df.columns if "precip" in c.lower()), None)
    e_col = next((c for c in df.columns if "evap" in c.lower() or "et" in c.lower()), None)
    t_col = next((c for c in df.columns if "temp" in c.lower() or "t2m" in c.lower()), None)

    recent = df.tail(min(len(df), 12))
    scale = 12.0 / max(len(recent), 1)
    precip_12m = float(recent[p_col].astype(float).sum() * scale) if p_col else 240.0
    evap_12m = float(abs(recent[e_col].astype(float).sum()) * scale) if e_col else 1150.0
    mean_temp = float(recent[t_col].astype(float).mean()) if t_col else 13.5

    aridity_ratio = round(precip_12m / max(evap_12m, 1.0), 4)
    climate_stress_score = float(np.clip((1.0 - min(aridity_ratio / 0.35, 1.0)) * 100.0, 0.0, 100.0))

    return {
        "source_mode": "timeseries_12m_window",
        "records_analyzed": int(len(recent)),
        "annual_equiv_precip_mm": round(precip_12m, 2),
        "annual_equiv_evap_mm": round(evap_12m, 2),
        "mean_temp_c": round(mean_temp, 2),
        "p_to_e_ratio": aridity_ratio,
        "climate_stress_score_0_100": round(climate_stress_score, 1),
    }


def evaluate_ecological_and_dust_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """ارزیابی یکپارچه وضعیت اکولوژیک، بستر خشک و شاخص ریسک گردوغبار نمکی"""
    current = payload.get("current_status", payload.get("latest_observation", {}))
    curve = payload.get("hypsometric_curve", [])

    cur_level = float(current.get("water_level_m", current.get("level_m", 1269.755)))
    cur_area = float(current.get("surface_area_km2", current.get("area_km2", 404.79)))
    cur_vol = float(current.get("volume_km3", current.get("storage_km3", 0.241)))

    if curve:
        eco_ref = interpolate_hypsometry(curve, ECOLOGICAL_TARGET_LEVEL_M)
        eco_area = eco_ref["area_km2"]
        eco_vol = eco_ref["volume_km3"]
        max_hist_area = eco_ref["max_historical_area_km2"]
    else:
        eco_area = 4340.0
        eco_vol = 14.5
        max_hist_area = 5800.0

    exposed_vs_ecological_km2 = max(0.0, eco_area - cur_area)
    exposed_vs_historical_max_km2 = max(0.0, max_hist_area - cur_area)
    desiccation_fraction_eco = min(1.0, exposed_vs_ecological_km2 / max(eco_area, 1.0))

    salinity_info = compute_salinity_and_artemia_status(cur_vol)

    era5_raw = (
        payload.get("era5_climate")
        or payload.get("climate_era5")
        or payload.get("climate_drivers")
        or payload.get("era5_summary")
        or {}
    )
    climate_info = compute_climate_stress(era5_raw)

    # شاخص ترکیبی ریسک گردوغبار نمکی (۶۵٪ سهم سطح بستر نمکی خشک‌شده + ۳۵٪ تنش خشکی اقلیمی)
    dust_index = round(
        0.65 * (desiccation_fraction_eco * 100.0)
        + 0.35 * climate_info["climate_stress_score_0_100"],
        1,
    )

    if dust_index >= 80.0:
        hazard_tier = "EXTREME"
    elif dust_index >= 60.0:
        hazard_tier = "HIGH"
    elif dust_index >= 35.0:
        hazard_tier = "MODERATE"
    else:
        hazard_tier = "LOW"

    return {
        "ecological_benchmark": {
            "target_level_m": ECOLOGICAL_TARGET_LEVEL_M,
            "target_area_km2": eco_area,
            "target_volume_km3": eco_vol,
            "level_deficit_m": round(cur_level - ECOLOGICAL_TARGET_LEVEL_M, 3),
            "volume_deficit_km3": round(cur_vol - eco_vol, 3),
            "water_volume_retention_pct": round((cur_vol / max(eco_vol, 0.01)) * 100.0, 2),
        },
        "exposed_lakebed_playa": {
            "current_wet_area_km2": round(cur_area, 2),
            "exposed_salt_playa_vs_ecological_km2": round(exposed_vs_ecological_km2, 2),
            "exposed_bed_vs_max_historical_km2": round(exposed_vs_historical_max_km2, 2),
            "desiccation_ratio_vs_ecological_pct": round(desiccation_fraction_eco * 100.0, 2),
        },
        "salinity_and_biology": salinity_info,
        "climate_stress": climate_info,
        "salt_dust_hazard": {
            "index_0_100": dust_index,
            "hazard_tier": hazard_tier,
            "primary_hotspot_zones": [
                "Eastern Salt Flats (Sharafkhaneh-Rahmanlu Axis)",
                "Southern Shallow Basin (Miandoab-Bokan Delta)",
                "Jabbarlu-Bonab Exposed Margin",
            ],
        },
    }
