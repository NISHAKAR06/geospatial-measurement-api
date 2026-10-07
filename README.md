---
 Geospatial Measurement API

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Package Manager](https://img.shields.io/badge/uv-Astral-purple?logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![Geospatial](https://img.shields.io/badge/Geospatial-GeoPandas%20%7C%20Shapely%20%7C%20PyProj-green)](https://geopandas.org/)
[![Status](https://img.shields.io/badge/Status-Under%20Development-orange)]()

A modern backend service for ingesting geospatial datasets, extracting spatial vector features, handling Coordinate Reference Systems (CRS), and computing accurate geometric measurements.

Built with **FastAPI**, **GeoPandas**, and **uv**, focusing on clean software architecture, type safety, modular design, and robust geospatial data processing.
---
## Table of Contents

- [Overview](#overview)
- [Supported Geometries &amp; Measurements](#supported-geometries--measurements)
- [Architecture &amp; Processing Flow](#architecture--processing-flow)
- [CRS Handling &amp; Transformation Engine](#crs-handling--transformation-engine)
- [API Reference](#api-reference)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation &amp; Setup](#installation--setup)
  - [Running the Server](#running-the-server)
- [Development Roadmap](#development-roadmap)
- [Design Goals](#design-goals)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Overview

Geographic files often bundle diverse coordinate spaces, mixed geometry types, and varying metadata standards. The **Geospatial Measurement API** automates the ingestion, validation, transformation, and measurement extraction of vector spatial files:

- **KML** (`.kml`) — Open standard XML format for geographical visualization.
- **Shapefile Archive** (`.zip`) — Multi-file shapefile bundles (`.shp`, `.shx`, `.dbf`, `.prj`).

The service parses input files into structured spatial features, normalizes coordinate reference frames, computes metric measurements (areas and lengths), and persists results for querying via RESTful endpoints.

---

## Supported Geometries & Measurements

| Geometry Type                           | Measurement Extracted | Output Unit             | Notes                              |
| --------------------------------------- | --------------------- | ----------------------- | ---------------------------------- |
| **Point**                         | *None*              | N/A                     | Coordinate position only           |
| **LineString**                    | **Length**      | Meters ($m$)          | Geodesic / projected path distance |
| **Polygon**                       | **Area**        | Square meters ($m^2$) | Planar projected polygon enclosure |
| **MultiLineString** *(planned)* | **Length**      | Meters ($m$)          | Total aggregated segment length    |
| **MultiPolygon** *(planned)*    | **Area**        | Square meters ($m^2$) | Combined surface area              |

---

## Architecture & Processing Flow

The ingestion pipeline transforms raw geospatial file uploads through validation, coordinate normalization, and metric computation:

```text
       ┌────────────────────────┐
       │ Geospatial File Upload │
       │  (.kml / .zip shapefile)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │    File Validation     │ (MIME check, archive integrity, extension)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ Geospatial Extraction  │ (GeoPandas / Fiona)
       │  • Geometries          │
       │  • Feature Properties  │
       │  • Source CRS Metadata │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   CRS Engine & Reproj  │
       │  (Angular -> Metric)   │ (Transforms EPSG:4326 to optimal UTM / Projected CRS)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │  Measurement Engine    │
       │  • Polygon  -> Area    │
       │  • Line     -> Length  │
       │  • Point    -> Position│
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Storage & Response   │
       │  (PostgreSQL/PostGIS)  │ (JSON REST payload)
       └────────────────────────┘
```

---

## CRS Handling & Transformation Engine

Geographic Coordinate Reference Systems such as **WGS 84 (`EPSG:4326`)** use angular units (degrees latitude and longitude). Computing geometric lengths and areas directly on degrees produces mathematically invalid, distorted results.

To ensure metric accuracy:

1. **Source CRS Detection**: Inspects projection metadata (`.prj` or KML coordinate headers). Defaults to `EPSG:4326` when unprojected lat/lon coordinates are detected.
2. **Dynamic Projected CRS Selection**: Determines an appropriate projected coordinate system (such as the local **Universal Transverse Mercator (UTM)** zone or equal-area projection) based on the feature centroid.
3. **Reprojection & Calculation**: Reprojects geometries into the target metric CRS and evaluates measurements in standard SI units:
   - **Length**: meters ($m$)
   - **Area**: square meters ($m^2$)

```text
Geographic CRS (degrees)  ──►  Reprojection Engine  ──►  Projected CRS (meters)  ──►  Accurate Measurements
   (e.g., EPSG:4326)                (PyProj)                    (e.g., UTM)                 (m / m²)
```

---

## API Reference

Interactive Swagger documentation is available locally at `http://127.0.0.1:8000/docs`.

### Root & Health Check

```http
GET /
```

**Response (`200 OK`):**

```json
{
  "message": "Welcome to the Geospatial Measurement API. Use the /measure endpoint to calculate measurements from geospatial files."
}
```

### File Upload

```http
POST /api/files/
```

Upload a `.kml` or `.zip` shapefile archive for asynchronous or synchronous processing.

**Form Data:**

- `file`: `multipart/form-data` (Binary stream)

**Response (`201 Created`):**

```json
{
  "file_id": "c8b42f2b-4398-4c12-9856-ff719e761dfa",
  "filename": "parcels_boundary.zip",
  "feature_count": 42,
  "source_crs": "EPSG:4326",
  "status": "processed"
}
```

### File Metadata

```http
GET /api/files/{id}/
```

Retrieve details, parsing status, and geometry summary of an uploaded file.

**Response (`200 OK`):**

```json
{
  "id": "c8b42f2b-4398-4c12-9856-ff719e761dfa",
  "filename": "parcels_boundary.zip",
  "source_crs": "EPSG:4326",
  "geometry_summary": {
    "Polygon": 30,
    "LineString": 10,
    "Point": 2
  },
  "created_at": "2026-10-07T11:40:00Z"
}
```

### Feature Measurements

```http
GET /api/files/{id}/measurements/
```

Retrieve computed measurements for each feature within the file.

**Response (`200 OK`):**

```json
{
  "file_id": "c8b42f2b-4398-4c12-9856-ff719e761dfa",
  "projected_crs": "EPSG:32632",
  "features": [
    {
      "feature_id": 1,
      "geometry_type": "Polygon",
      "measurement_type": "area",
      "value": 15420.75,
      "unit": "square_meters",
      "properties": {
        "name": "Zone A Parcel"
      }
    },
    {
      "feature_id": 2,
      "geometry_type": "LineString",
      "measurement_type": "length",
      "value": 312.4,
      "unit": "meters",
      "properties": {
        "name": "Main Access Road"
      }
    },
    {
      "feature_id": 3,
      "geometry_type": "Point",
      "measurement_type": null,
      "value": null,
      "unit": null,
      "properties": {
        "name": "Survey Benchmark"
      }
    }
  ]
}
```

---

## Technology Stack

| Domain                          | Technology                                                                     | Purpose                                                 |
| ------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------- |
| **Web Framework**         | [FastAPI](https://fastapi.tiangolo.com/)                                        | High-performance async REST API framework               |
| **Validation & Settings** | [Pydantic v2](https://docs.pydantic.dev/)                                       | Strict data validation and schema enforcement           |
| **ASGI Server**           | [Uvicorn](https://www.uvicorn.org/)                                             | Lightning-fast ASGI production web server               |
| **Spatial Processing**    | [GeoPandas](https://geopandas.org/) & [Shapely](https://shapely.readthedocs.io/) | Vector geometries, dataframes, spatial algebra          |
| **Projections / CRS**     | [PyProj](https://pyproj4.github.io/pyproj/)                                     | Cartographic projections and coordinate transformations |
| **Database & ORM**        | [PostgreSQL](https://www.postgresql.org/) + [PostGIS](https://postgis.net/)      | Spatial relational database persistence                 |
| **ORM**                   | [SQLAlchemy 2.0](https://www.sqlalchemy.org/)                                   | Type-safe database models and sessions                  |
| **Testing**               | [Pytest](https://docs.pytest.org/)                                              | Unit and integration test suite                         |
| **Package Manager**       | [uv](https://github.com/astral-sh/uv)                                           | Ultra-fast Python package and venv manager              |
| **Containerization**      | [Docker](https://www.docker.com/) & Docker Compose                              | Reproducible multi-service deployment                   |

---

## Project Structure

```text
geospatial-measurement-api/
│
├── app/
│   ├── api/             # API route handlers and endpoints
│   │   └── v1/
│   ├── core/            # App configuration, logging, and security
│   ├── db/              # Database connection session and PostGIS setup
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request and response schemas
│   ├── services/        # Business logic (File parsing, CRS, Measurements)
│   │   ├── crs.py
│   │   ├── parser.py
│   │   └── measurement.py
│   ├── repositories/    # Database queries and persistence layer
│   └── main.py          # FastAPI application entrypoint
│
├── tests/               # Unit, integration, and geometry test suites
├── sample_data/         # KML and Shapefile sample fixtures
├── uploads/             # Temporary file staging directory
│
├── Dockerfile           # Production container specification
├── docker-compose.yml   # Multi-container setup (API + PostGIS)
├── pyproject.toml       # Python dependencies and project metadata
├── uv.lock              # Deterministic dependency lockfile
└── README.md            # Project documentation
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- [**uv**](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- **Git**
- **Docker** *(required for PostGIS database stage)*

### Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/NISHAKAR06/geospatial-measurement-api.git
   cd geospatial-measurement-api
   ```
2. **Create a virtual environment:**

   ```bash
   uv venv --python 3.12
   ```
3. **Activate the environment:**

   - **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
4. **Install dependencies:**

   ```bash
   uv sync
   ```

### Running the Server

Start the development server with live reload:

```bash
uv run uvicorn app.main:app --reload
```

The service will be accessible at:

- **Base API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## Development Roadmap

- [X] **Phase 1 — Backend Foundation**
  - FastAPI application structure & basic configuration
  - `uv` package management setup
  - Base health check endpoint
- [ ] **Phase 2 — Geospatial Fundamentals**
  - Geometry validation structures (Point, LineString, Polygon)
  - GeoPandas and Fiona data loading pipelines
- [ ] **Phase 3 — File Ingestion & Validation**
  - KML parsing engine
  - Shapefile `.zip` archive decompression & file validation
  - Spatial feature and attribute extraction
- [ ] **Phase 4 — Measurement Engine**
  - Planar polygon area calculations
  - LineString length calculations
  - Graceful handling of unsupported geometry types
- [ ] **Phase 5 — CRS Engine**
  - Source CRS detection and validation
  - Auto-detection of optimal projected CRS (UTM zones)
  - PyProj reprojection pipelines
- [ ] **Phase 6 — Persistence**
  - PostgreSQL & PostGIS database integration via SQLAlchemy
  - Metadata and spatial feature storage
- [ ] **Phase 7 — API Endpoints**
  - Upload (`POST /api/files/`)
  - File status (`GET /api/files/{id}/`)
  - Measurement retrieval (`GET /api/files/{id}/measurements/`)
- [ ] **Phase 8 — Automated Testing**
  - Pytest test suite for geometry edge cases, CRS transformations, and API contracts
- [ ] **Phase 9 — Production Deployment**
  - Multi-stage Docker build with GDAL/GEOS support
  - Docker Compose setup with PostGIS

---

## Design Goals

- **Separation of Concerns**: Clean modular layer separation between API routing, spatial business logic, and database persistence.
- **Geospatial Precision**: No naive calculations on angular coordinates; reliable metric reprojection.
- **Strict Data Validation**: Pydantic v2 schemas and validation for both file inputs and API responses.
- **Maintainability & Typing**: Full type annotations throughout the codebase.
- **Automated Testing**: Comprehensive unit and integration test coverage for all spatial algorithms.

---

## Future Enhancements

- Support for additional spatial formats: **GeoJSON**, **GeoPackage** (`.gpkg`), and **FlatGeobuf**.
- Multi-geometry support (`MultiPolygon`, `MultiLineString`, `GeometryCollection`).
- Background job processing for large datasets with Celery/Redis.
- Cloud object storage integration (AWS S3 / Google Cloud Storage) for uploaded files.
- Interactive web map visualization (Leaflet / MapLibre) in frontend preview.

---

## License

This project is licensed under the [MIT License](LICENSE).
-----------------------------------------------
