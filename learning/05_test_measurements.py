from app.services.file_processor import process_file
from app.services.measurement import calculate_measurements


file_path = "sample_data/sample_shapefile.zip"

gdf = process_file(file_path)

results = calculate_measurements(gdf)

print("\n--- Measurement Results ---")

for result in results:
    print(result)