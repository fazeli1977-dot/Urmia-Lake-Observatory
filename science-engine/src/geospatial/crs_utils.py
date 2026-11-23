"""Coordinate Reference System (CRS) utilities for metric area and length computation."""

from typing import Tuple
import pyproj
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from shapely.validation import make_valid

from src.config.urmia_config import GEOGRAPHIC_CRS_EPSG, METRIC_CRS_EPSG

_TO_UTM38N = pyproj.Transformer.from_crs(
    GEOGRAPHIC_CRS_EPSG, METRIC_CRS_EPSG, always_xy=True
).transform

_TO_WGS84 = pyproj.Transformer.from_crs(
    METRIC_CRS_EPSG, GEOGRAPHIC_CRS_EPSG, always_xy=True
).transform


def ensure_valid_geometry(geom: BaseGeometry) -> BaseGeometry:
    """Repair self-intersections or ring orientation issues deterministically."""
    if geom.is_valid:
        return geom
    return make_valid(geom)


def project_to_utm38n(geom_wgs84: BaseGeometry) -> BaseGeometry:
    """Project a WGS84 (EPSG:4326) geometry to UTM Zone 38N (EPSG:32638) in meters."""
    valid_geom = ensure_valid_geometry(geom_wgs84)
    return transform(_TO_UTM38N, valid_geom)


def project_to_wgs84(geom_utm: BaseGeometry) -> BaseGeometry:
    """Project a UTM Zone 38N (EPSG:32638) geometry back to WGS84 (EPSG:4326)."""
    valid_geom = ensure_valid_geometry(geom_utm)
    return transform(_TO_WGS84, valid_geom)


def compute_area_perimeter_km(geom_wgs84: BaseGeometry) -> Tuple[float, float]:
    """Return (area_km2, perimeter_km) computed strictly in EPSG:32638."""
    geom_m = project_to_utm38n(geom_wgs84)
    area_km2 = round(geom_m.area / 1_000_000.0, 2)
    perimeter_km = round(geom_m.length / 1_000.0, 2)
    return area_km2, perimeter_km


def compute_length_km(geom_wgs84: BaseGeometry) -> float:
    """Return linear length in kilometers computed strictly in EPSG:32638."""
    geom_m = project_to_utm38n(geom_wgs84)
    return round(geom_m.length / 1_000.0, 2)