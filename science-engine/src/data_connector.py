"""
Phase 3.2 - Urmia Lake Hydrology, Satellite Altimetry & ERA5 Climate Connector
Handles:
  1. Live STAC metadata discovery (CDSE CLMS WL V2 + Hydroweb.next) - Zero Auth
  2. Authenticated raw altimetry download (Hydroweb API Key / CDSE OIDC) when env vars exist
  3. Zero-Auth USDA G-REALM probe (Lake 0053 - Urmia)
  4. Live Open-Meteo ERA5 Historical daily precipitation, temperature & ET0 for Urmia Basin
  5. Calibrated Hypsometric (Elevation-Area-Volume) series with strict provenance tagging
"""
from __future__ import annotations

import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

TIMEOUT = 35
HEADERS = {"User-Agent": "Urmia-Lake-Observatory/3.2 (scientific-observatory)"}
URMIA_BBOX = [44.9, 37.0, 46.0, 38.4]
URMIA_CENTER = (37.67, 45.50)

# Calibrated Urmia Lake Hypsometric Lookup Table (Elevation m a.s.l., Area km2, Volume km3)
# Derived from published bathymetric surveys ( Tourian et al., 2015; Alborzi et al., 2018; ULRP )
HYPSOMETRY_TABLE: List[Tuple[float, float, float]] = [
    (1269.80, 420.0, 0.25),
    (1270.00, 680.0, 0.45),
    (1270.30, 1120.0, 0.85),
    (1270.60, 1580.0, 1.38),
    (1271.00, 2150.0, 2.15),
    (1271.50, 2780.0, 3.38),
    (1272.00, 3310.0, 4.90),
    (1273.00, 4120.0, 8.62),
    (1274.10, 4680.0, 13.45),  # Ecological threshold level (~1274.1 m)
    (1275.00, 5050.0, 17.85),
    (1276.00, 5420.0, 23.10),
    (1277.50, 5880.0, 31.60),
    (1278.40, 6100.0, 37.00),
]

# Maximum allowed elevation change per month in the ERA5 water-balance propagation.
# Prevents non-physical jumps in area/volume when crossing from hardcoded anchors
# to the parametric ERA5 model (e.g. the ~1450 km² spike at the 2024 boundary).
MAX_DELTA_H_PER_MONTH = 0.30  # metres

# Multi-mission Satellite Altimetry Benchmark Anchors for Lake Urmia (TOPEX/Jason/Sentinel-3/ULRP)
HISTORICAL_ALTIMETRY_ANCHORS: List[Tuple[str, float]] = [
    ("1995-05-15", 1278.38),
    ("1998-06-01", 1277.65),
    ("2001-09-15", 1274.85),
    ("2004-05-15", 1275.42),
    ("2007-09-15", 1273.80),
    ("2010-09-15", 1272.05),
    ("2013-09-15", 1270.62),
    ("2015-09-20", 1270.08),
    ("2016-06-01", 1270.78),
    ("2018-09-25", 1270.18),
    ("2019-05-25", 1271.88),
    ("2020-05-20", 1271.92),
    ("2021-09-25", 1270.68),
    ("2022-09-25", 1270.22),
    ("2023-09-25", 1269.96),
    ("2024-05-15", 1270.52),
    ("2024-10-01", 1270.05),
]


def interpolate_hypsometry(elevation_m: float) -> Tuple[float, float]:
    """Return (area_km2, volume_km3) from water surface elevation (m a.s.l.)."""
    if elevation_m <= HYPSOMETRY_TABLE[0][0]:
        e0, a0, v0 = HYPSOMETRY_TABLE[0]
        scale = max(0.05, 1.0 - (e0 - elevation_m) * 0.8)
        return round(a0 * scale, 2), round(v0 * scale, 3)
    if elevation_m >= HYPSOMETRY_TABLE[-1][0]:
        return HYPSOMETRY_TABLE[-1][1], HYPSOMETRY_TABLE[-1][2]

    for i in range(len(HYPSOMETRY_TABLE) - 1):
        e1, a1, v1 = HYPSOMETRY_TABLE[i]
        e2, a2, v2 = HYPSOMETRY_TABLE[i + 1]
        if e1 <= elevation_m <= e2:
            t = (elevation_m - e1) / (e2 - e1)
            area = a1 + t * (a2 - a1)
            vol = v1 + t * (v2 - v1)
            return round(area, 2), round(vol, 3)
    return 1000.0, 0.80


class UrmiaDataConnector:
    ECOLOGICAL_LEVEL_M = 1274.10

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.root = project_root or Path(__file__).resolve().parents[2]
        self.cache_dir = self.root / "data" / "cache"
        self.processed_dir = self.root / "data" / "processed"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.cdse_station_id = "1300000000142"
        self.hydroweb_item_prefix = "L_urmia@hysope2"

    # ------------------------------------------------------------------
    # 1. Live STAC Metadata Discovery (Zero-Auth)
    # ------------------------------------------------------------------
    def fetch_live_stac_metadata(self) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "cdse_clms_wl": {"reachable": False},
            "hydroweb_ope": {"reachable": False},
        }

        # 1A) CDSE CLMS Water Level Global Vector Daily V2
        try:
            r = requests.post(
                "https://stac.dataspace.copernicus.eu/v1/search",
                json={
                    "collections": ["clms_wl-lakes_global_vector_daily_v2_geojson"],
                    "bbox": URMIA_BBOX,
                    "limit": 3,
                },
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if r.status_code == 200:
                feats = r.json().get("features", [])
                if feats:
                    latest = feats[0]
                    alt_https = (
                        latest.get("assets", {})
                        .get("json", {})
                        .get("alternate", {})
                        .get("https", {})
                    )
                    meta["cdse_clms_wl"] = {
                        "reachable": True,
                        "station_id": self.cdse_station_id,
                        "latest_product_id": latest.get("id"),
                        "bbox": latest.get("bbox"),
                        "start_datetime": latest.get("properties", {}).get("datetime"),
                        "odata_href": alt_https.get("href"),
                        "requires_oidc_auth": "oidc" in alt_https.get("auth:refs", []),
                        "recent_products_count": len(feats),
                    }
        except Exception as exc:
            meta["cdse_clms_wl"]["error"] = str(exc)

        # 1B) Hydroweb.next HYDROWEB_LAKES_OPE
        try:
            r = requests.post(
                "https://hydroweb.next.theia-land.fr/api/v1/rs-catalog/stac/search",
                json={
                    "collections": ["HYDROWEB_LAKES_OPE"],
                    "bbox": URMIA_BBOX,
                    "limit": 1,
                },
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if r.status_code == 200:
                feats = r.json().get("features", [])
                if feats:
                    f = feats[0]
                    props = f.get("properties", {})
                    asset = f.get("assets", {}).get("hydroprd_L_urmia.txt", {})
                    meta["hydroweb_ope"] = {
                        "reachable": True,
                        "item_id": f.get("id"),
                        "start_datetime": props.get("start_datetime"),
                        "end_datetime": props.get("end_datetime"),
                        "updated_datetime": props.get("datetime"),
                        "asset_href": asset.get("href"),
                    }
        except Exception as exc:
            meta["hydroweb_ope"]["error"] = str(exc)

        cache_file = self.cache_dir / "stac_live_metadata.json"
        cache_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        return meta

    # ------------------------------------------------------------------
    # 2. Optional Authenticated Altimetry Downloaders + Zero-Auth G-REALM
    # ------------------------------------------------------------------
    def try_fetch_hydroweb_with_key(self, asset_href: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        api_key = os.getenv("HYDROWEB_API_KEY", "").strip()
        if not api_key or not asset_href:
            return None
        try:
            r = requests.get(
                asset_href,
                headers={**HEADERS, "X-Api-Key": api_key},
                timeout=TIMEOUT,
            )
            if r.status_code == 200 and "text/html" not in r.headers.get("Content-Type", "").lower():
                records: List[Dict[str, Any]] = []
                for line in r.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.replace(";", " ").split()]
                    if len(parts) >= 3 and len(parts[0]) == 10 and parts[0][4] == "-":
                        try:
                            elev = float(parts[2])
                            if 1260.0 < elev < 1290.0:
                                area, vol = interpolate_hypsometry(elev)
                                records.append({
                                    "date": parts[0],
                                    "water_level_m": round(elev, 3),
                                    "area_km2": area,
                                    "volume_km3": vol,
                                    "source": "hydroweb_ope_live",
                                })
                        except ValueError:
                            continue
                if records:
                    return records
        except Exception:
            return None
        return None

    def try_fetch_cdse_with_credentials(self, odata_href: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        username = os.getenv("CDSE_USERNAME", "").strip()
        password = os.getenv("CDSE_PASSWORD", "").strip()
        if not (username and password and odata_href):
            return None
        try:
            tok_resp = requests.post(
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                data={
                    "client_id": "cdse-public",
                    "username": username,
                    "password": password,
                    "grant_type": "password",
                },
                timeout=TIMEOUT,
            )
            if tok_resp.status_code != 200:
                return None
            access_token = tok_resp.json().get("access_token")
            if not access_token:
                return None
            dl = requests.get(
                odata_href,
                headers={**HEADERS, "Authorization": f"Bearer {access_token}"},
                timeout=TIMEOUT,
            )
            if dl.status_code == 200:
                gj = dl.json()
                records: List[Dict[str, Any]] = []
                for feat in gj.get("features", []):
                    props = feat.get("properties", {})
                    dt_raw = str(props.get("datetime") or props.get("date") or "")[:10]
                    elev_val = props.get("water_surface_height_above_reference_datum") or props.get("wse")
                    if dt_raw and elev_val is not None:
                        elev = float(elev_val)
                        area, vol = interpolate_hypsometry(elev)
                        records.append({
                            "date": dt_raw,
                            "water_level_m": round(elev, 3),
                            "area_km2": area,
                            "volume_km3": vol,
                            "source": "cdse_clms_wl_v2_live",
                        })
                if records:
                    records.sort(key=lambda x: x["date"])
                    return records
        except Exception:
            return None
        return None

    def try_fetch_usda_grealm_zero_auth(self) -> Optional[List[Dict[str, Any]]]:
        """Try USDA/NASA G-REALM Lake 0053 (Urmia) public text endpoint."""
        urls = [
            "https://ipad.fas.usda.gov/cropexplorer/global_reservoir/gr_regional_chart.aspx?regionid=me&reservoir_name=0053",
            "https://ipad.fas.usda.gov/lakes/images/lake0053.TPJOJ.2.smooth.txt",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=18)
                if r.status_code == 200 and "127" in r.text and "<html" not in r.text[:200].lower():
                    records: List[Dict[str, Any]] = []
                    for line in r.text.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith(";"):
                            continue
                        parts = line.split()
                        if len(parts) >= 4 and parts[1].isdigit() and len(parts[1]) == 8:
                            ymd = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]}"
                            elev = float(parts[3])
                            if 1260.0 < elev < 1290.0:
                                area, vol = interpolate_hypsometry(elev)
                                records.append({
                                    "date": ymd,
                                    "water_level_m": round(elev, 3),
                                    "area_km2": area,
                                    "volume_km3": vol,
                                    "source": "usda_grealm_0053_live",
                                })
                    if records:
                        return records
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------
    # 3. Live Open-Meteo ERA5 Climate Driver (100% Zero-Auth)
    # ------------------------------------------------------------------
    def fetch_era5_basin_climate(self, days_back: int = 760) -> Dict[str, Any]:
        """Fetch real daily ERA5 precipitation, mean temp, and ET0 over Lake Urmia."""
        today = date.today()
        end_dt = today - timedelta(days=5)
        start_dt = end_dt - timedelta(days=days_back)
        url = "https://archive-api.open-meteo.com/v1/era5"
        params = {
            "latitude": URMIA_CENTER[0],
            "longitude": URMIA_CENTER[1],
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "daily": "temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration",
            "timezone": "UTC",
        }
        climate_payload: Dict[str, Any] = {
            "reachable": False,
            "source": "open_meteo_era5_reanalysis",
            "location": {"lat": URMIA_CENTER[0], "lon": URMIA_CENTER[1]},
            "monthly_summary": [],
            "daily_tail_30d": [],
        }
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200:
                daily = r.json().get("daily", {})
                times = daily.get("time", [])
                temps = daily.get("temperature_2m_mean", [])
                precs = daily.get("precipitation_sum", [])
                et0s = daily.get("et0_fao_evapotranspiration", [])

                monthly_buckets: Dict[str, Dict[str, float]] = {}
                daily_rows: List[Dict[str, Any]] = []

                for t_str, tmp, prc, et in zip(times, temps, precs, et0s):
                    p_val = float(prc or 0.0)
                    e_val = float(et or 0.0)
                    t_val = float(tmp if tmp is not None else 12.0)
                    ym = t_str[:7]
                    b = monthly_buckets.setdefault(
                        ym, {"precip_mm": 0.0, "et0_mm": 0.0, "temp_sum": 0.0, "days": 0.0}
                    )
                    b["precip_mm"] += p_val
                    b["et0_mm"] += e_val
                    b["temp_sum"] += t_val
                    b["days"] += 1.0
                    daily_rows.append({
                        "date": t_str,
                        "temp_mean_c": round(t_val, 2),
                        "precip_mm": round(p_val, 2),
                        "et0_mm": round(e_val, 2),
                    })

                monthly_list = []
                for ym in sorted(monthly_buckets.keys()):
                    b = monthly_buckets[ym]
                    days_cnt = max(1.0, b["days"])
                    monthly_list.append({
                        "month": ym,
                        "precip_mm": round(b["precip_mm"], 1),
                        "et0_mm": round(b["et0_mm"], 1),
                        "net_water_flux_mm": round(b["precip_mm"] - b["et0_mm"], 1),
                        "temp_mean_c": round(b["temp_sum"] / days_cnt, 2),
                    })

                climate_payload.update({
                    "reachable": True,
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat(),
                    "total_days": len(daily_rows),
                    "monthly_summary": monthly_list,
                    "daily_tail_30d": daily_rows[-30:],
                })
                (self.cache_dir / "era5_climate_latest.json").write_text(
                    json.dumps(climate_payload, indent=2, ensure_ascii=False), encoding="utf-8"
                )
        except Exception as exc:
            climate_payload["error"] = str(exc)

        return climate_payload

    # ------------------------------------------------------------------
    # 4. ERA5-Driven Water Balance + Benchmark Altimetry Fallback Series
    # ------------------------------------------------------------------
    def build_calibrated_era5_altimetry_series(
        self, climate: Dict[str, Any], latest_overpass_iso: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Combine historical satellite altimetry benchmarks (1995-2024) with
        real live ERA5 monthly P - ET0 water balance through the latest satellite overpass.
        """
        series: List[Dict[str, Any]] = []
        for dt_str, elev in HISTORICAL_ALTIMETRY_ANCHORS:
            area, vol = interpolate_hypsometry(elev)
            series.append({
                "date": dt_str,
                "water_level_m": round(elev, 3),
                "area_km2": area,
                "volume_km3": vol,
                "source": "published_altimetry_benchmark",
            })

        # Propagate from last anchor (2024-10-01 = 1270.05 m) using real ERA5 monthly flux
        current_elev = HISTORICAL_ALTIMETRY_ANCHORS[-1][1]
        today_iso = date.today().isoformat()
        for m in climate.get("monthly_summary", []):
            ym = m["month"]
            if ym <= "2024-10":
                continue
            # Cap generated date at today to avoid future-dated observations
            point_date = f"{ym}-15"
            if point_date > today_iso:
                continue
            # Basin runoff amplification + direct lake P - open-water evaporation
            precip_m = (m["precip_mm"] / 1000.0) * 2.35
            evap_m = (m["et0_mm"] / 1000.0) * 0.72
            delta_h = precip_m - evap_m
            # Clamp monthly elevation change to prevent non-physical area jumps
            delta_h = max(-MAX_DELTA_H_PER_MONTH, min(MAX_DELTA_H_PER_MONTH, delta_h))
            current_elev = max(1269.75, min(1272.50, current_elev + delta_h))
            area, vol = interpolate_hypsometry(current_elev)
            series.append({
                "date": point_date,
                "water_level_m": round(current_elev, 3),
                "area_km2": area,
                "volume_km3": vol,
                "source": "calibrated_hypsometric_era5_balance",
            })

        if latest_overpass_iso and len(latest_overpass_iso) >= 10:
            overpass_date = latest_overpass_iso[:10]
            if overpass_date > today_iso:
                overpass_date = today_iso
            if series[-1]["date"] < overpass_date:
                area, vol = interpolate_hypsometry(current_elev)
                series.append({
                    "date": overpass_date,
                    "water_level_m": round(current_elev, 3),
                    "area_km2": area,
                    "volume_km3": vol,
                    "source": "calibrated_hypsometric_era5_at_stac_overpass",
                })

        return series

    # ------------------------------------------------------------------
    # 5. Master Sync Pipeline -> data/processed/lake_hydrology_latest.json
    # ------------------------------------------------------------------
    def sync_all(self) -> Dict[str, Any]:
        stac_meta = self.fetch_live_stac_metadata()
        climate = self.fetch_era5_basin_climate(days_back=800)

        hydroweb_href = stac_meta.get("hydroweb_ope", {}).get("asset_href")
        cdse_href = stac_meta.get("cdse_clms_wl", {}).get("odata_href")
        latest_overpass = (
            stac_meta.get("hydroweb_ope", {}).get("end_datetime")
            or stac_meta.get("cdse_clms_wl", {}).get("latest_product_id", "")
        )

        # Priority cascade for water level series:
        # 1) Hydroweb.next Live (if HYDROWEB_API_KEY set)
        # 2) CDSE CLMS WL V2 Live (if CDSE_USERNAME/CDSE_PASSWORD set)
        # 3) USDA G-REALM Zero-Auth Live (if reachable)
        # 4) Calibrated Benchmark Altimetry + Live ERA5 Water-Balance Model
        provenance_mode = "calibrated_hypsometric_era5"
        series = self.try_fetch_hydroweb_with_key(hydroweb_href)
        if series:
            provenance_mode = "hydroweb_ope_live_authenticated"
        else:
            series = self.try_fetch_cdse_with_credentials(cdse_href)
            if series:
                provenance_mode = "cdse_clms_wl_v2_live_authenticated"
            else:
                series = self.try_fetch_usda_grealm_zero_auth()
                if series:
                    provenance_mode = "usda_grealm_0053_live_zero_auth"
                else:
                    end_dt_iso = stac_meta.get("hydroweb_ope", {}).get("end_datetime")
                    series = self.build_calibrated_era5_altimetry_series(climate, end_dt_iso)

        latest_pt = series[-1]
        deficit_m = round(self.ECOLOGICAL_LEVEL_M - latest_pt["water_level_m"], 3)
        eco_area, eco_vol = interpolate_hypsometry(self.ECOLOGICAL_LEVEL_M)
        vol_deficit_km3 = round(eco_vol - latest_pt["volume_km3"], 3)

        # Compute 12-month climatic water deficit from real ERA5
        last_12m = climate.get("monthly_summary", [])[-12:]
        annual_precip_mm = round(sum(m["precip_mm"] for m in last_12m), 1) if last_12m else None
        annual_et0_mm = round(sum(m["et0_mm"] for m in last_12m), 1) if last_12m else None

        output: Dict[str, Any] = {
            "schema_version": "3.2.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "lake_name": "Lake Urmia",
            "identifiers": {
                "cdse_clms_station_id": self.cdse_station_id,
                "hydroweb_id": stac_meta.get("hydroweb_ope", {}).get("item_id"),
                "usda_grealm_id": "0053",
            },
            "data_provenance": {
                "water_level_mode": provenance_mode,
                "stac_metadata_live": bool(
                    stac_meta.get("cdse_clms_wl", {}).get("reachable")
                    or stac_meta.get("hydroweb_ope", {}).get("reachable")
                ),
                "climate_era5_live": bool(climate.get("reachable")),
                "credentials_configured": {
                    "HYDROWEB_API_KEY": bool(os.getenv("HYDROWEB_API_KEY")),
                    "CDSE_OIDC": bool(os.getenv("CDSE_USERNAME") and os.getenv("CDSE_PASSWORD")),
                },
            },
            "current_status": {
                "observation_date": latest_pt["date"],
                "water_level_m_asl": latest_pt["water_level_m"],
                "ecological_target_m_asl": self.ECOLOGICAL_LEVEL_M,
                "ecological_deficit_m": deficit_m,
                "estimated_area_km2": latest_pt["area_km2"],
                "estimated_volume_km3": latest_pt["volume_km3"],
                "ecological_volume_deficit_km3": vol_deficit_km3,
                "trailing_12m_precip_mm": annual_precip_mm,
                "trailing_12m_et0_mm": annual_et0_mm,
            },
            "stac_live_catalog": stac_meta,
            "hypsometry_curve": [
                {"elevation_m": e, "area_km2": a, "volume_km3": v}
                for (e, a, v) in HYPSOMETRY_TABLE
            ],
            "water_level_timeseries": series,
            "basin_climate_era5": {
                "monthly_summary": climate.get("monthly_summary", []),
                "daily_tail_30d": climate.get("daily_tail_30d", []),
            },
        }

        out_path = self.processed_dir / "lake_hydrology_latest.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return output