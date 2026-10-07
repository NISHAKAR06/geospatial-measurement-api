import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

point =Point(77.5946, 12.9716)  # Example coordinates for Bangalore, India

line = LineString([
    (77.5946, 12.9716),
    (77.5960, 12.9730),
    (77.5980, 12.9745),
])

polygon = Polygon([
    (77.5946, 12.9716),
    (77.6000, 12.9716),
    (77.6000, 12.9760),
    (77.5946, 12.9760),
    (77.5946, 12.9716),
])

data = {
    "name": [
        "Survey Point",
        "Access Road",
        "Mining Area",
    ],
    "type": [
        "survey",
        "road",
        "mining",
    ],
    "geometry": [
        point,
        line,
        polygon,
    ],
}

gdf =gpd.GeoDataFrame(
    data, 
    geometry="geometry",
    crs="EPSG:4326"
    )  # WGS84 coordinate reference system

print(gdf)

print("\n--- Geometry Types ---")
print(gdf.geometry.geom_type)

print("\n--- CRS ---")
print(gdf.crs)

print("\n--- Columns ---")
print(gdf.columns)

print("\n--- Number of Features ---")
print(len(gdf))

print("\n--- Direct Measurements ---")

point_geometry = gdf.iloc[0].geometry
line_geometry = gdf.iloc[1].geometry
polygon_geometry = gdf.iloc[2].geometry

print("Point:", point_geometry)
print("Line length:", line_geometry.length)
print("Polygon area:", polygon_geometry.area)


print("\n--- CRS Transformation ---")

projected_gdf = gdf.to_crs("EPSG:32643")

print("Original CRS:", gdf.crs)
print("Projected CRS:", projected_gdf.crs)

print("\n--- Projected Geometry ---")
print(projected_gdf.geometry)

print("\n--- Projected Measurements ---")

projected_line = projected_gdf.iloc[1].geometry
projected_polygon = projected_gdf.iloc[2].geometry

print("Line length (metres):", projected_line.length)
print("Polygon area (square metres):", projected_polygon.area)
