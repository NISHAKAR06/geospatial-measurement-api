from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon


output_dir = Path("sample_data/shapefile")
output_dir.mkdir(parents=True, exist_ok=True)


geometries = [
    Point(77.5946, 12.9716),
    LineString([
        (77.5946, 12.9716),
        (77.5960, 12.9730),
        (77.5980, 12.9745),
    ]),
    Polygon([
        (77.5946, 12.9716),
        (77.6000, 12.9716),
        (77.6000, 12.9760),
        (77.5946, 12.9760),
        (77.5946, 12.9716),
    ]),
]


gdf = gpd.GeoDataFrame(
    {
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
    },
    geometry=geometries,
    crs="EPSG:4326",
)


output_path = output_dir / "sample.shp"

gdf.to_file(output_path, driver="ESRI Shapefile")

print(f"Shapefile created at: {output_path}")