from pathlib import Path
import zipfile
import geopandas as gpd
from shapely.geometry import Polygon


output_dir = Path("sample_data/shapefile")
output_dir.mkdir(parents=True, exist_ok=True)

# Create multiple distinct Polygon features
geometries = [
    # Polygon 1: Mining Block A
    Polygon([
        (77.5946, 12.9716),
        (77.6000, 12.9716),
        (77.6000, 12.9760),
        (77.5946, 12.9760),
        (77.5946, 12.9716),
    ]),
    # Polygon 2: Processing Zone
    Polygon([
        (77.6010, 12.9716),
        (77.6050, 12.9716),
        (77.6050, 12.9750),
        (77.6010, 12.9750),
        (77.6010, 12.9716),
    ]),
    # Polygon 3: Environmental Buffer
    Polygon([
        (77.5946, 12.9770),
        (77.6050, 12.9770),
        (77.6050, 12.9800),
        (77.5946, 12.9800),
        (77.5946, 12.9770),
    ]),
]

gdf = gpd.GeoDataFrame(
    {
        "name": [
            "Mining Block A",
            "Processing Zone",
            "Environmental Buffer",
        ],
        "zone_type": [
            "extraction",
            "processing",
            "conservation",
        ],
        "priority": [
            1,
            2,
            3,
        ],
    },
    geometry=geometries,
    crs="EPSG:4326",
)

output_shp = output_dir / "sample.shp"
gdf.to_file(output_shp, driver="ESRI Shapefile")
print(f"Shapefile created at: {output_shp}")

# Create ZIP archive containing .shp, .shx, .dbf, .prj
zip_path = Path("sample_data/sample_shapefile.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
    for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
        file_to_add = output_dir / f"sample{ext}"
        if file_to_add.exists():
            zip_file.write(file_to_add, arcname=f"sample{ext}")

print(f"ZIP archive created at: {zip_path}")