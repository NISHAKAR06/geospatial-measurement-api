# 🌐 Geospatial Measurement API

<p align="center">
  <strong>A high-performance, CRS-aware REST service for geospatial data ingestion, feature extraction, and metric spatial calculations.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/Packaging-uv-DE5FE9?style=flat-square&logo=astral&logoColor=white" alt="uv"></a>
  <a href="https://geopandas.org/"><img src="https://img.shields.io/badge/Geospatial-GeoPandas%20%7C%20Shapely%20%7C%20PyProj-2C5E3B?style=flat-square" alt="Geospatial"></a>
  <a href="https://postgis.net/"><img src="https://img.shields.io/badge/Database-PostgreSQL%20%2F%20PostGIS-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostGIS"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Status-Assignment%20Ready-blue?style=flat-square" alt="Status">
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#processing-flow">Processing Flow</a> •
  <a href="#crs-strategy">CRS Strategy</a> •
  <a href="#api-documentation">API Documentation</a> •
  <a href="#setup--local-development">Setup & Development</a> •
  <a href="#testing">Testing</a> •
  <a href="#design-decisions">Design Decisions</a> •
  <a href="#key-learnings">Key Learnings</a> •
  <a href="#future-scope">Future Scope</a>
</p>

---

## Overview

Geographic datasets arrive in varying vector file formats, fragmented coordinate systems, and unprojected angular coordinate frames. The **Geospatial Measurement API** is an automated backend service designed to solve these challenges through robust validation, intelligent coordinate transformations, and metric geometric calculations:

- **KML Support** (`.kml`): Parses Placemarks into vector features, attributes, and geometries.
- **Shapefile ZIP Support** (`.zip`): Ingests zipped ESRI Shapefiles (`.shp`, `.shx`, `.dbf`, `.prj`) with strict security protections against path traversal (Zip Slip) and resource exhaustion attacks. Shapefiles without CRS metadata (`.prj`) are rejected because reliable metric area and length calculations require a known Coordinate Reference System.
- **Feature Extraction**: Extracts discrete geometric features, their primitive types (`Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, `MultiPolygon`), GeoJSON representations, and associated attribute properties.
- **CRS Handling**: Accurately detects source Coordinate Reference Systems (CRS) and dynamically reprojects geographic coordinates into optimal metric projected systems before measuring.
- **Measurement Calculation**: Computes polygon areas ($m^2$) and line lengths ($m$) in standardized metric units while gracefully handling non-dimensional point entities.
- **PostgreSQL / PostGIS Persistence**: Stores file metadata, non-spatial attribute dictionaries as `JSONB`, and spatial vector geometries in standard WGS84 PostGIS columns with GIST spatial indexing.

---

## Architecture

The service adheres to a modular, layered backend architecture separating API handling, pure geospatial domain logic, and relational spatial persistence:

```text
Client
  │
  ▼
FastAPI (app/api/files.py)
  │
  ├───► File Processor (app/services/file_processor.py)
  │       • File & Archive Validation
  │       • Zip Slip Security Checks
  │       • GeoPandas / Fiona Vector Parsing
  │
  ├───► Measurement Service (app/services/measurement.py)
  │       • Source CRS Inspection
  │       • Dynamic UTM Reprojection (PyProj)
  │       • Vector Geometric Measurements & Repair (Shapely)
  │       • GeoJSON Geometry Serialization
  │
  └───► Persistence Service (app/services/persistence.py)
          • Transaction Management
          • PostGIS Spatial Serialization (GeoAlchemy2)
          • GIST Spatial Indexing & JSONB Attribute Storage
          │
          ▼
PostgreSQL + PostGIS (Docker / Relational Database)
```

---

## Processing Flow

Every uploaded dataset traverses an atomic, validated processing lifecycle:

```text
Upload
  ↓
Validate (Format, Extension, Size limit)
  ↓
Save Temporary File
  ↓
Parse (GeoPandas KML / Shapefile reader)
  ↓
Extract Features & Properties
  ↓
Determine Source CRS
  ↓
Transform CRS (Geographic → Optimal Local UTM Projected CRS)
  ↓
Measure (Area in m², Length in m, Point handling)
  ↓
Persist (Database transaction in PostgreSQL / PostGIS)
  ↓
Clean Temporary Files
  ↓
Return Response (File ID, CRS details, feature count)
```

---

## CRS Strategy

### The Fundamental Geospatial Problem
Geographic Coordinate Reference Systems such as **WGS 84 (`EPSG:4326`)** express locations on an oblate spheroid in **angular degrees** (latitude and longitude).
- Angular degrees do not possess a uniform physical length. At the equator, $1^\circ$ of longitude is approximately $111.32\text{ km}$, but at $60^\circ$ latitude it shrinks to approximately $55.80\text{ km}$, and at the poles it converges to $0\text{ km}$.
- Performing Euclidean distance or area formulas ($\sqrt{\Delta x^2 + \Delta y^2}$ or shoelace formula) on coordinates in degrees yields mathematically invalid, non-uniform results with meaningless units ($\text{degrees}^2$).

### Coordinate Transformation (`to_crs()` vs. `set_crs()`)
- **`set_crs()`**: Defines or overrides the CRS metadata without modifying the actual coordinate numbers. Using `set_crs()` on geographic data to treat it as projected corrupts the geometry because degrees are falsely interpreted as meters.
- **`to_crs()`**: Applies rigorous mathematical cartographic transformations to project angular ellipsoidal coordinates into a Cartesian flat plane with true metric coordinates ($x, y$ in meters).

### Dynamic Projection Workflow
The service transforms coordinates into a suitable metric projected CRS before measurement, ensuring area and distance calculations are strictly performed on metric coordinates ($m, m^2$):

1. **Inspection**: Verify that `gdf.crs` is present. If missing, the file is rejected with a validation error. Shapefiles require a `.prj` component to resolve their CRS.
2. **Linear Unit Classification**:
   - **Geographic CRS** (e.g. `EPSG:4326`): Coordinates are in angular degrees. The service estimates an optimal local **Universal Transverse Mercator (UTM)** metric zone via `gdf.estimate_utm_crs()` and reprojects coordinates into it.
   - **Metric Projected CRS** (e.g. UTM, Web Mercator): The coordinate system's linear unit is already metric (metres). The CRS and coordinates are preserved without unnecessary transformation.
   - **Non-Metric Projected CRS** (e.g. State Plane in US survey feet or international feet): Linear units are not metres. The service transforms coordinates into a suitable metric projected CRS (such as UTM) before measuring, preventing feet from being erroneously labeled as metres.
3. **Measurement Invariance**: API measurements are always calculated on Cartesian metric coordinates and returned in meters ($m$) for length and square meters ($m^2$) for area.
4. **Auditing**: Both `original_crs` and `measurement_crs` are recorded and returned for auditability and reproducibility.

**Projection Scope & Trade-offs:**
- Universal Transverse Mercator (UTM) provides a conformal Cartesian system designed for local and regional zones ($6^\circ$ longitude strips). Within its designated zone, scale distortion is minimal (typically $< 0.1\%$).
- For large continental datasets spanning multiple UTM zones, equal-area projections (such as Albers Equal Area) may be required to maintain consistent surface area metrics.
- High-latitude/polar regions or datasets crossing the antimeridian require specialized polar stereographic or azimuthal projections.

---

## Supported Geometries & Measurements

| Geometry Type | Measurement Extracted | Output Unit | Behavior |
|:---|:---:|:---:|:---|
| **Point** | *None* | `null` | Position recorded as GeoJSON; no dimension calculated |
| **MultiPoint** | *None* | `null` | Positions recorded as GeoJSON; no dimension calculated |
| **LineString** | **Length** | Meters ($m$) | Metric distance along segment vertices |
| **MultiLineString** | **Length** | Meters ($m$) | Aggregated sum of all segment lengths |
| **Polygon** | **Area** | Square meters ($m^2$) | Surface area of exterior ring minus interior holes |
| **MultiPolygon** | **Area** | Square meters ($m^2$) | Aggregated sum of all polygon components |
| **Empty Geometry** | *None* | `null` | Returns `status: "EMPTY_GEOMETRY"` |
| **GeometryCollection** | *None* | `null` | Returns `status: "NOT_SUPPORTED"` |

---

## API Documentation

Interactive Swagger documentation is available at **`http://localhost:8000/docs`** and ReDoc at **`http://localhost:8000/redoc`**.

### 1. Root & Health Check

```http
GET /
```
**Response (`200 OK`):**
```json
{
  "message": "Geospatial Measurement API is running"
}
```

```http
GET /health
```
**Response (`200 OK`):**
```json
{
  "status": "ok"
}
```

---

### 2. Upload Geospatial File

```http
POST /api/files/
Content-Type: multipart/form-data
```

Accepts `.kml` or `.zip` shapefile archives.

**Example `cURL` Request:**
```bash
curl -X POST "http://localhost:8000/api/files/" \
     -H "accept: application/json" \
     -F "file=@sample_data/sample.kml;type=application/vnd.google-earth.kml+xml"
```

**Response (`201 Created`):**
```json
{
  "id": "e229e06d-e462-4b2a-a99f-7232e0e4708d",
  "filename": "sample.kml",
  "original_crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "feature_count": 3,
  "status": "COMPLETED",
  "created_at": "2026-10-08T12:00:00Z"
}
```

---

### 3. Retrieve File Metadata

```http
GET /api/files/{id}/
```

**Example `cURL` Request:**
```bash
curl -X GET "http://localhost:8000/api/files/e229e06d-e462-4b2a-a99f-7232e0e4708d/" \
     -H "accept: application/json"
```

**Response (`200 OK`):**
```json
{
  "id": "e229e06d-e462-4b2a-a99f-7232e0e4708d",
  "filename": "sample.kml",
  "crs": "EPSG:4326",
  "original_crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "feature_count": 3,
  "status": "COMPLETED",
  "created_at": "2026-10-08T12:00:00Z"
}
```

---

### 4. Retrieve Computed Feature Measurements

```http
GET /api/files/{id}/measurements/
```

**Example `cURL` Request:**
```bash
curl -X GET "http://localhost:8000/api/files/e229e06d-e462-4b2a-a99f-7232e0e4708d/measurements/" \
     -H "accept: application/json"
```

**Response (`200 OK`):**
```json
{
  "file_id": "e229e06d-e462-4b2a-a99f-7232e0e4708d",
  "original_crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Point",
      "geometry": {
        "type": "Point",
        "coordinates": [77.5946, 12.9716]
      },
      "crs": "EPSG:4326",
      "measurement": null,
      "properties": {
        "Name": "Survey Point"
      }
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [77.5946, 12.9716],
          [77.596, 12.973],
          [77.598, 12.9745]
        ]
      },
      "measurement": {
        "type": "length",
        "value": 490.39,
        "unit": "m",
        "status": "OK"
      },
      "properties": {
        "Name": "Access Road"
      }
    },
    {
      "feature_id": 2,
      "geometry_type": "Polygon",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [77.5946, 12.9716],
            [77.6, 12.9716],
            [77.6, 12.976],
            [77.5946, 12.976],
            [77.5946, 12.9716]
          ]
        ]
      },
      "measurement": {
        "type": "area",
        "value": 285522.44,
        "unit": "m²",
        "status": "OK"
      },
      "properties": {
        "Name": "Mining Area"
      }
    }
  ]
}
```

---

## Setup & Local Development

### Prerequisites

- **Python 3.12**
- [**uv**](https://docs.astral-sh/uv/) (Fast Python package manager)
- **Docker & Docker Compose** (for PostgreSQL / PostGIS)

### 1. Clone the Repository

```bash
git clone https://github.com/NISHAKAR06/geospatial-measurement-api.git
cd geospatial-measurement-api
```

### 2. Install Dependencies

Using `uv`:

```bash
uv sync
```

### 3. Environment Configuration

Copy the example environment configuration:

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

### 4. Start PostGIS Database Container

```bash
docker compose up -d db
```

### 5. Run Database Migrations

Apply Alembic migrations to initialize PostGIS extensions and tables:

```bash
uv run alembic upgrade head
```

### 6. Start the API Server

Launch the development server with auto-reload:

```bash
uv run uvicorn app.main:app --reload
```

The application is now live at **`http://localhost:8000`**.

---

## Docker Deployment Workflow

To build and run both PostGIS and the API container via Docker Compose:

1. **Start the database container**:
   ```bash
   docker compose up -d db
   ```

2. **Execute Alembic migrations using the API container**:
   ```bash
   docker compose run --rm api alembic upgrade head
   ```

3. **Start the API service**:
   ```bash
   docker compose up -d api
   ```

4. **Verify container health**:
   ```bash
   docker compose ps
   ```

---

## Testing

The project includes an automated test suite covering file processing, security constraints (Zip Slip protection), measurement logic, CRS transformations, GeoJSON serialization, and REST API contracts.

Run all tests via `pytest`:

```bash
uv run pytest -v
```

---

## Design Decisions

- **FastAPI**: Provides asynchronous endpoint handling, automatic OpenAPI/Swagger documentation, and high concurrency.
- **GeoPandas & Fiona**: Standardized spatial data abstraction providing reliable vector parsing for both KML and Shapefile formats.
- **Shapely & PyProj**: Delivers robust 2D Cartesian spatial operations, `make_valid()` geometry repair, and geodetic coordinate transformations.
- **PostgreSQL / PostGIS**: Relational storage with native spatial indexing (GIST `idx_features_geometry`) and a unique constraint on `(file_id, feature_index)`.
- **UTM Estimation Strategy**: Uses `estimate_utm_crs()` based on centroid coordinates to dynamically select the exact 6-degree UTM zone, minimizing projection distortion.
- **Temporary File Isolation & Security**: Uploaded files and Shapefile extractions are handled in isolated `NamedTemporaryFile` and `TemporaryDirectory` environments with guaranteed teardown.
- **Zip Slip & Bomb Protection**: Archive inspection rejects path traversal sequences (`..`, leading slashes) and caps entries at 500 files and 200MB uncompressed size.
- **JSONB Attribute Storage**: Non-spatial feature properties are dynamically mapped to PostgreSQL `JSONB`, accommodating arbitrary attribute columns without requiring hard-coded schema alterations.

---

## Key Learnings

1. **Geospatial Coordinate Integrity**: Calculating distance and area directly on angular degrees (`EPSG:4326`) produces mathematically invalid results because degrees vary with latitude. Dynamically projecting into conformal Cartesian systems (such as local UTM zones) ensures mathematically sound Euclidean operations.
2. **Linear Unit Variance in Projected CRSs**: Not all projected systems use SI meters; regional coordinate frames (such as US State Plane `EPSG:2263`) utilize US survey feet. Inspecting coordinate axis metadata (`axis_info`) guarantees coordinates are converted to metric frames before applying Euclidean formulas.
3. **Defensive Archive Ingestion (Zip Slip)**: Unzipping user-submitted Shapefile archives requires strict path traversal defense (rejecting `..`, absolute paths, and excessive entry counts) to protect the host operating system from file overwrites.
4. **Automated Topology Healing**: Real-world aerial geometries frequently feature self-intersections or bowtie loops. Using GEOS-backed `shapely.make_valid()` provides automated topological repair without corrupting spatial features.
5. **Dual Spatial Indexing**: Combining relational composite constraints `(file_id, feature_index)` with PostGIS GIST spatial indexing (`idx_features_geometry`) ensures high performance across both relational lookups and bounding-box spatial filters.

---

## Future Scope

- **Asynchronous / Background Task Ingestion**: Offloading multi-gigabyte spatial files and raster orthomosaics to background queues using Celery and Redis.
- **Extended Spatial Formats**: Ingestion support for **GeoPackage** (`.gpkg`), **FlatGeobuf**, and Cloud-Optimized GeoTIFFs (COG).
- **Spatial Filtering & Bounding Box Queries**: Exposing spatial query endpoints (e.g. `GET /api/features?bbox=...` or spatial intersects) utilizing the underlying PostGIS GIST index.
- **Cloud Object Storage**: Direct presigned upload integration with Amazon S3 or Google Cloud Storage for large archive processing.
- **Authentication & Rate Limiting**: Production API key or OAuth2/JWT access controls with token bucket rate limiting.

---

## License

This project is licensed under the [MIT License](LICENSE).
