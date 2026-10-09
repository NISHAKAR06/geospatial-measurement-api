import geopandas as gpd
import pytest
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from app.services.measurement import (
    calculate_measurement,
    calculate_measurements,
    geometry_to_geojson,
    is_metric_crs,
    prepare_for_measurement,
)


def test_calculate_measurement_point():
    point = Point(77.5946, 12.9716)
    assert calculate_measurement(point) is None


def test_calculate_measurement_multipoint():
    mp = MultiPoint([(77.5946, 12.9716), (77.5950, 12.9720)])
    assert calculate_measurement(mp) is None


def test_calculate_measurement_linestring():
    line = LineString([(0, 0), (100, 0)])
    res = calculate_measurement(line)
    assert res is not None
    assert res["type"] == "length"
    assert res["value"] == 100.0
    assert res["unit"] == "m"
    assert res["status"] == "OK"


def test_calculate_measurement_multilinestring():
    mls = MultiLineString([
        [(0, 0), (50, 0)],
        [(50, 0), (100, 0)],
    ])
    res = calculate_measurement(mls)
    assert res is not None
    assert res["type"] == "length"
    assert res["value"] == 100.0
    assert res["unit"] == "m"
    assert res["status"] == "OK"


def test_calculate_measurement_polygon():
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    res = calculate_measurement(poly)
    assert res is not None
    assert res["type"] == "area"
    assert res["value"] == 10000.0
    assert res["unit"] == "m²"
    assert res["status"] == "OK"


def test_calculate_measurement_multipolygon():
    poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])  # 100 m²
    poly2 = Polygon([(20, 0), (30, 0), (30, 10), (20, 10), (20, 0)])  # 100 m²
    mpoly = MultiPolygon([poly1, poly2])
    res = calculate_measurement(mpoly)
    assert res is not None
    assert res["type"] == "area"
    assert res["value"] == 200.0
    assert res["unit"] == "m²"
    assert res["status"] == "OK"


def test_calculate_measurement_unsupported_geometry():
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
    res = calculate_measurement(gc)
    assert res is not None
    assert res["status"] == "NOT_SUPPORTED"
    assert res["value"] is None


def test_calculate_measurement_empty_geometry():
    empty_poly = Polygon()
    res = calculate_measurement(empty_poly)
    assert res is not None
    assert res["status"] == "EMPTY_GEOMETRY"


def test_calculate_measurement_none_geometry():
    res = calculate_measurement(None)
    assert res is not None
    assert res["status"] == "INVALID_GEOMETRY"


def test_calculate_measurement_invalid_geometry_repaired():
    # Self-intersecting bowtie polygon (invalid)
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    assert not bowtie.is_valid
    res = calculate_measurement(bowtie)
    assert res is not None
    # make_valid() repairs it into a valid MultiPolygon, so it calculates area
    assert res["type"] == "area"
    assert res["status"] == "OK"
    assert res["value"] > 0


def test_geometry_to_geojson():
    p = Point(77.5946, 12.9716)
    geojson = geometry_to_geojson(p)
    assert geojson is not None
    assert geojson["type"] == "Point"
    assert geojson["coordinates"] == (77.5946, 12.9716)

    # None and empty geometries
    assert geometry_to_geojson(None) is None
    assert geometry_to_geojson(Polygon()) is None


def test_missing_crs_raises_error():
    gdf = gpd.GeoDataFrame(
        {"name": ["Test"]},
        geometry=[Point(0, 0)],
        crs=None,
    )
    with pytest.raises(ValueError, match="does not contain a CRS"):
        prepare_for_measurement(gdf)


def test_geographic_crs_transformed_to_projected():
    gdf = gpd.GeoDataFrame(
        {"name": ["Bangalore Point"]},
        geometry=[Point(77.5946, 12.9716)],
        crs="EPSG:4326",
    )
    meas_gdf, orig_crs, meas_crs = prepare_for_measurement(gdf)
    assert orig_crs == "EPSG:4326"
    assert meas_crs.startswith("EPSG:326")  # UTM zone 43N
    assert not meas_gdf.crs.is_geographic


def test_already_projected_crs_preserved():
    # UTM Zone 43N (EPSG:32643)
    gdf = gpd.GeoDataFrame(
        {"name": ["Projected Point"]},
        geometry=[Point(781523.4, 1435211.2)],
        crs="EPSG:32643",
    )
    meas_gdf, orig_crs, meas_crs = prepare_for_measurement(gdf)
    assert orig_crs == "EPSG:32643"
    assert meas_crs == "EPSG:32643"
    assert meas_gdf.crs.to_epsg() == 32643


def test_is_metric_crs():
    import pyproj

    assert is_metric_crs(pyproj.CRS("EPSG:32643")) is True  # UTM zone 43N (metres)
    assert is_metric_crs(pyproj.CRS("EPSG:3857")) is True   # Web Mercator (metres)
    assert is_metric_crs(pyproj.CRS("EPSG:2263")) is False  # State Plane NY (US survey feet)
    assert is_metric_crs(pyproj.CRS("EPSG:2913")) is False  # State Plane OR (international feet)
    assert is_metric_crs(pyproj.CRS("EPSG:4326")) is False  # Geographic (degrees)
    assert is_metric_crs(None) is False


def test_non_metre_projected_crs_transformed_to_metric():
    # EPSG:2263 is NAD83 / New York Long Island (ftUS), which uses US survey feet
    # 5,280 ftUS = 1 US survey mile = ~1609.344 meters
    # A 1,000 ftUS x 1,000 ftUS polygon = 1,000,000 ftUS² = ~92,903 m²
    line = LineString([(985000, 195000), (985000, 195000 + 5280)])
    poly = Polygon([
        (985000, 195000),
        (986000, 195000),
        (986000, 196000),
        (985000, 196000),
        (985000, 195000),
    ])
    gdf = gpd.GeoDataFrame(
        {"name": ["Survey Line", "Survey Parcel"]},
        geometry=[line, poly],
        crs="EPSG:2263",
    )

    results, orig_crs, meas_crs = calculate_measurements(gdf)

    # 1. Original CRS is preserved in original_crs
    assert orig_crs == "EPSG:2263"

    # 2. Measurement CRS is transformed to a metric CRS (e.g. UTM zone 18N / EPSG:32618)
    assert meas_crs != "EPSG:2263"
    assert meas_crs.startswith("EPSG:326")

    # 3. Resulting measurement is reported in "m" for length
    line_meas = results[0]["measurement"]
    assert line_meas["type"] == "length"
    assert line_meas["unit"] == "m"
    assert line_meas["status"] == "OK"
    # 5. Calculation does not simply treat feet as metres (5280 ft != 5280 m; ~1608.85 m)
    assert 1600.0 < line_meas["value"] < 1620.0
    assert line_meas["value"] != 5280.0

    # 4. Area is reported in "m²"
    poly_meas = results[1]["measurement"]
    assert poly_meas["type"] == "area"
    assert poly_meas["unit"] == "m²"
    assert poly_meas["status"] == "OK"
    # 5. 1,000,000 sq ft != 1,000,000 m²; ~92,845 m²
    assert 90000.0 < poly_meas["value"] < 95000.0
    assert poly_meas["value"] != 1000000.0



def test_calculate_measurements_batch():
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Point A", "Line B", "Parcel C"],
            "category": ["survey", "transport", "land"],
        },
        geometry=[
            Point(77.5946, 12.9716),
            LineString([(77.5946, 12.9716), (77.5960, 12.9730)]),
            Polygon([(77.5946, 12.9716), (77.6000, 12.9716), (77.6000, 12.9760), (77.5946, 12.9760), (77.5946, 12.9716)]),
        ],
        crs="EPSG:4326",
    )
    results, orig_crs, meas_crs = calculate_measurements(gdf)
    assert len(results) == 3
    assert orig_crs == "EPSG:4326"
    assert meas_crs.startswith("EPSG:326")
    assert results[0]["measurement"] is None
    assert results[1]["measurement"]["type"] == "length"
    assert results[1]["measurement"]["value"] > 0
    assert results[2]["measurement"]["type"] == "area"
    assert results[2]["measurement"]["value"] > 0
