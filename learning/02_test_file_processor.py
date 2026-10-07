from app.services.file_processor import process_file


file_path = "sample_data/sample.kml"

gdf = process_file(file_path)

print(gdf)

print("\n--- CRS ---")
print(gdf.crs)

print("\n--- Geometry Types ---")
print(gdf.geometry.geom_type)

print("\n--- Feature Count ---")
print(len(gdf))