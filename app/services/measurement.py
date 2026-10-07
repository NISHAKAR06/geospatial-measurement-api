import geopandas as gpd


def prepare_for_measurement(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Prepare geospatial data for accurate distance/area measurement.

    Geographic CRS (latitude/longitude) cannot be used directly for
    measurements because its units are degrees. If the input data uses
    a geographic CRS, estimate a suitable UTM projected CRS and
    transform the geometries into it.
    """

    if gdf.empty:
        raise ValueError("Geospatial dataset is empty.")

    if gdf.crs is None:
        raise ValueError(
            "Input geospatial data does not contain a CRS."
        )

    # Already projected: coordinates are already in a projected unit
    # such as metres, so no transformation is required.
    if not gdf.crs.is_geographic:
        return gdf

    # Estimate an appropriate UTM CRS from the dataset's location.
    projected_crs = gdf.estimate_utm_crs()

    if projected_crs is None:
        raise ValueError(
            "Unable to determine a suitable projected CRS."
        )

    return gdf.to_crs(projected_crs)


def calculate_measurement(geometry) -> dict | None:
    """
    Calculate the appropriate measurement for one geometry.

    Point:
        No measurement required.

    LineString:
        Calculate length in metres.

    Polygon:
        Calculate area in square metres.

    Unsupported geometry:
        Return a structured NOT_SUPPORTED response.
    """

    if geometry is None:
        return {
            "type": None,
            "value": None,
            "unit": None,
            "status": "INVALID_GEOMETRY",
        }

    geometry_type = geometry.geom_type

    if geometry.is_empty:
        return {
            "type": None,
            "value": None,
            "unit": None,
            "status": "EMPTY_GEOMETRY",
        }

    if geometry_type == "Point":
        return None

    if geometry_type == "LineString":
        return {
            "type": "length",
            "value": geometry.length,
            "unit": "m",
            "status": "OK",
        }

    if geometry_type == "Polygon":
        return {
            "type": "area",
            "value": geometry.area,
            "unit": "m²",
            "status": "OK",
        }

    return {
        "type": None,
        "value": None,
        "unit": None,
        "status": "NOT_SUPPORTED",
    }


def calculate_measurements(
    gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """
    Calculate measurements for every feature in a GeoDataFrame.
    """

    measurement_gdf = prepare_for_measurement(gdf)

    results = []

    for index, geometry in measurement_gdf.geometry.items():

        measurement = calculate_measurement(geometry)

        results.append(
            {
                "feature_id": index,
                "geometry_type": geometry.geom_type
                if geometry is not None
                else None,
                "measurement": measurement,
            }
        )

    return results