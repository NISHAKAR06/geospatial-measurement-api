---
noteId: "f6f7dce0c33811f187ee4105bc4ebbfb"
tags: []

---

# 📂 Production Geospatial Datasets

This directory contains production-ready test datasets modeled after real-world drone inspection, infrastructure mapping, and cadastral surveying workflows (e.g. Aereo enterprise missions).

---

## 🗂 Available Production Datasets (`sample_data/production/`)

| File Name | Format | Coordinate System (CRS) | Geometry Types | Features | Real-World Scenario |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`drone_solar_farm_survey.kml`** | `.kml` | `EPSG:4326` (WGS 84) | `Point`, `LineString`, `Polygon` | 6 | Pavagada Solar Park UAV aerial photogrammetry survey with RTK Ground Control Points (GCPs), serpentine flight lines, access road, and 50MW solar blocks (including an inverter exclusion donut hole). |
| **`infrastructure_transmission_lines_wgs84.zip`** | `.zip` (Shapefile) | `EPSG:4326` (WGS 84) | `LineString` | 4 | Regional electrical utility corridor with 400kV lines, 220kV feeder lines, maintenance trails, and fiber-optic ties with voltage and conductor attributes. |
| **`cadastral_parcels_utm43n.zip`** | `.zip` (Shapefile) | `EPSG:32643` (UTM 43N Metric) | `Polygon`, `MultiPolygon` | 4 | Heavy industrial estate cadastral land plots with zoning classifications, floor-area-ratio (FAR) attributes, and disjoint factory multi-polygons. Coordinates already in metric meters. |
| **`gas_pipeline_corridor_feet.zip`** | `.zip` (Shapefile) | `EPSG:2263` (State Plane NY ftUS) | `LineString` | 3 | High-pressure natural gas transmission pipeline alignment in US survey feet. Automatically converts from feet to meters (`EPSG:32618`) before measuring. |
| **`ground_control_points_wgs84.zip`** | `.zip` (Shapefile) | `EPSG:4326` (WGS 84) | `Point` | 5 | Aerial survey ground control points (GCPs), check points, and GNSS base station coordinates with millimeter accuracy tags. |

---

## 🚀 How to Test & Upload via cURL

### 1. Upload KML Drone Solar Farm Survey
```bash
curl -X POST "http://localhost:8000/api/files/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_data/production/drone_solar_farm_survey.kml"
```

### 2. Upload Shapefile Archive (UTM 43N Metric)
```bash
curl -X POST "http://localhost:8000/api/files/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_data/production/cadastral_parcels_utm43n.zip"
```

### 3. Upload State Plane Shapefile (US Survey Feet)
```bash
curl -X POST "http://localhost:8000/api/files/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_data/production/gas_pipeline_corridor_feet.zip"
```

### 4. Fetch Measurements
Replace `<FILE_ID>` with the `id` returned from the upload response:
```bash
curl -X GET "http://localhost:8000/api/files/<FILE_ID>/measurements/"
```

---

## 🔄 Re-generating or Extending the Datasets

To regenerate or customize any of these datasets, run:
```bash
uv run python scripts/generate_production_data.py
```

To run the offline automated verification across all production datasets:
```bash
uv run python scripts/verify_production_data.py
```
