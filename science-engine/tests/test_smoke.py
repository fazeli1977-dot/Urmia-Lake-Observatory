"""Phase 1 smoke tests verifying Python geospatial & scientific environment."""

import numpy as np
import pyproj
import rasterio
import shapely
from shapely.geometry import box

from src.config.urmia_config import (
    ECOLOGICAL_TARGET_LEVEL_MASL,
    GEOGRAPHIC_CRS_EPSG,
    LAKE_URMIA_BBOX,
    METRIC_CRS_EPSG,
    URMIA_BASIN_BBOX,
)


def test_urmia_bbox_containment() -> None:
    lake_geom = box(*LAKE_URMIA_BBOX.as_bbox())
    basin_geom = box(*URMIA_BASIN_BBOX.as_bbox())
    assert basin_geom.contains(lake_geom), "Basin bbox must strictly contain Lake Urmia bbox."


def test_crs_projection_utm38n() -> None:
    transformer = pyproj.Transformer.from_crs(
        GEOGRAPHIC_CRS_EPSG, METRIC_CRS_EPSG, always_xy=True
    )
    # Approximate center of Lake Urmia (45.35 E, 37.65 N)
    easting, northing = transformer.transform(45.35, 37.65)
    assert 500_000 < easting < 600_000
    assert 4_100_000 < northing < 4_250_000


def test_core_libraries_loaded() -> None:
    arr = np.array([1270.0, ECOLOGICAL_TARGET_LEVEL_MASL], dtype=float)
    assert arr.shape == (2,)
    assert shapely.__version__ is not None
    assert rasterio.__version__ is not None