from typing import Any, Dict, List, Tuple
import math
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def format_crs_string(crs) -> str:
    """Format CRS as EPSG code if available, otherwise return CRS string."""
    if crs is None:
        return "Unknown"
    epsg = crs.to_epsg()
    if epsg is not None:
        return f"EPSG:{epsg}"
    return str(crs)


def prepare_for_measurement(
    gdf: gpd.GeoDataFrame,
) -> Tuple[gpd.GeoDataFrame, str, str]:
    """
    Prepare geospatial data for accurate distance and area calculations.

    Geographic Coordinate Reference Systems (such as WGS84 / EPSG:4326)
    use angular units (degrees) that cannot be used for Euclidean metric
    measurements. When geographic CRS is detected, an optimal local UTM
    projected CRS is dynamically estimated and applied.

    Returns:
        (measurement_gdf, original_crs_str, measurement_crs_str)
    """
    if gdf.empty:
        raise ValueError("Geospatial dataset is empty.")

    if gdf.crs is None:
        raise ValueError("Input geospatial data does not contain a CRS.")

    original_crs_str = format_crs_string(gdf.crs)

    if not gdf.crs.is_geographic:
        # Already projected into metric units
        return gdf, original_crs_str, original_crs_str

    # Estimate appropriate local UTM CRS based on dataset bounds/centroid
    projected_crs = gdf.estimate_utm_crs()

    if projected_crs is None:
        raise ValueError("Unable to determine a suitable projected CRS.")

    measurement_gdf = gdf.to_crs(projected_crs)
    measurement_crs_str = format_crs_string(projected_crs)

    return measurement_gdf, original_crs_str, measurement_crs_str


def calculate_measurement(geometry: BaseGeometry | None) -> dict | None:
    """
    Calculate the appropriate measurement for a single geometry.

    Rules:
    - Point / MultiPoint: No measurement (returns None).
    - LineString / MultiLineString: Length in metres.
    - Polygon / MultiPolygon: Area in square metres.
    - Empty geometry: EMPTY_GEOMETRY status.
    - Invalid or null geometry: INVALID_GEOMETRY status.
    - GeometryCollection or others: NOT_SUPPORTED status.
    """
    if geometry is None:
        return {
            "type": None,
            "value": None,
            "unit": None,
            "status": "INVALID_GEOMETRY",
        }

    if geometry.is_empty:
        return {
            "type": None,
            "value": None,
            "unit": None,
            "status": "EMPTY_GEOMETRY",
        }

    if not geometry.is_valid:
        # Attempt minimal repair if feasible, or mark invalid
        try:
            geometry = geometry.buffer(0)
            if not geometry.is_valid:
                return {
                    "type": None,
                    "value": None,
                    "unit": None,
                    "status": "INVALID_GEOMETRY",
                }
        except Exception:
            return {
                "type": None,
                "value": None,
                "unit": None,
                "status": "INVALID_GEOMETRY",
            }

    geom_type = geometry.geom_type

    if geom_type in ("Point", "MultiPoint"):
        return None

    if geom_type in ("LineString", "MultiLineString"):
        return {
            "type": "length",
            "value": round(float(geometry.length), 2),
            "unit": "m",
            "status": "OK",
        }

    if geom_type in ("Polygon", "MultiPolygon"):
        return {
            "type": "area",
            "value": round(float(geometry.area), 2),
            "unit": "m²",
            "status": "OK",
        }

    return {
        "type": None,
        "value": None,
        "unit": None,
        "status": "NOT_SUPPORTED",
    }


def sanitize_property_value(val: Any) -> Any:
    """Convert pandas/numpy values to JSON-serializable primitives."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val)
    return str(val)


def extract_properties(row: pd.Series, geometry_col: str = "geometry") -> Dict[str, Any]:
    """Extract non-geometry attribute properties from a row."""
    props = {}
    for col, val in row.items():
        if col == geometry_col:
            continue
        props[str(col)] = sanitize_property_value(val)
    return props


def calculate_measurements(
    gdf: gpd.GeoDataFrame,
) -> Tuple[List[Dict[str, Any]], str, str]:
    """
    Calculate measurements for every feature in a GeoDataFrame.

    Returns:
        (results_list, original_crs, measurement_crs)
    """
    measurement_gdf, original_crs_str, measurement_crs_str = prepare_for_measurement(gdf)

    results = []
    geom_col = gdf.geometry.name

    for idx, (original_idx, row) in enumerate(gdf.iterrows()):
        measured_geom = measurement_gdf.geometry.iloc[idx]
        original_geom = row[geom_col] if geom_col in row else None

        measurement = calculate_measurement(measured_geom)
        props = extract_properties(row, geometry_col=geom_col)

        results.append(
            {
                "feature_id": idx,
                "geometry_type": original_geom.geom_type if original_geom is not None and not original_geom.is_empty else None,
                "measurement": measurement,
                "properties": props,
            }
        )

    return results, original_crs_str, measurement_crs_str