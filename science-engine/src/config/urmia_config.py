"""Core geographic and scientific constants for Lake Urmia & Watershed."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GeographicBounds:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def as_bbox(self) -> Tuple[float, float, float, float]:
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


# Lake Urmia waterbody / playa core bounding box (WGS84 - EPSG:4326)
LAKE_URMIA_BBOX = GeographicBounds(
    min_lon=44.95,
    min_lat=37.00,
    max_lon=46.05,
    max_lat=38.35,
)

# Lake Urmia hydrological basin bounding box (WGS84 - EPSG:4326)
URMIA_BASIN_BBOX = GeographicBounds(
    min_lon=44.05,
    min_lat=35.65,
    max_lon=47.90,
    max_lat=38.55,
)

# Metric CRS for accurate area calculation in NW Iran: UTM Zone 38N
METRIC_CRS_EPSG = "EPSG:32638"
GEOGRAPHIC_CRS_EPSG = "EPSG:4326"

# Ecological reference level documented in scientific literature (m above sea level)
ECOLOGICAL_TARGET_LEVEL_MASL = 1274.1