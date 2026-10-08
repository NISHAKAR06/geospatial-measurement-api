import io
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.core.config import settings


def test_post_valid_kml(client: TestClient):
    kml_path = Path("sample_data/sample.kml")
    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")},
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample.kml"
    assert data["feature_count"] == 3
    assert data["original_crs"] == "EPSG:4326"
    assert data["measurement_crs"].startswith("EPSG:326")
    assert data["status"] == "COMPLETED"


def test_post_valid_shapefile_zip(client: TestClient):
    zip_path = Path("sample_data/sample_shapefile.zip")
    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_shapefile.zip", f, "application/zip")},
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_shapefile.zip"
    assert data["feature_count"] == 3
    assert data["status"] == "COMPLETED"


def test_post_unsupported_file(client: TestClient):
    response = client.post(
        "/api/files/",
        files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_post_file_too_large(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    # Set limit to 0 MB (effective < 1KB threshold) to test 413
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    oversized_data = b"A" * 1024
    response = client.post(
        "/api/files/",
        files={"file": ("sample.kml", io.BytesIO(oversized_data), "application/vnd.google-earth.kml+xml")},
    )
    assert response.status_code == 413
    assert "File size exceeds the maximum limit" in response.json()["detail"]


def test_get_file_details(client: TestClient):
    # Upload first
    kml_path = Path("sample_data/sample.kml")
    with open(kml_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/",
            files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")},
        )
    file_id = upload_resp.json()["id"]

    # Retrieve file
    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["filename"] == "sample.kml"
    assert data["feature_count"] == 3
    assert data["status"] == "COMPLETED"


def test_get_file_details_not_found(client: TestClient):
    random_id = uuid.uuid4()
    response = client.get(f"/api/files/{random_id}/")
    assert response.status_code == 404
    assert f"File with ID '{random_id}' was not found." in response.json()["detail"]


def test_get_file_measurements(client: TestClient):
    # Upload first
    kml_path = Path("sample_data/sample.kml")
    with open(kml_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/",
            files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")},
        )
    file_id = upload_resp.json()["id"]

    # Retrieve measurements
    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    measurements = data["measurements"]
    assert len(measurements) == 3

    # Point: measurement should be null
    assert measurements[0]["geometry_type"] == "Point"
    assert measurements[0]["measurement"] is None

    # LineString: length
    assert measurements[1]["geometry_type"] == "LineString"
    assert measurements[1]["measurement"]["type"] == "length"
    assert measurements[1]["measurement"]["value"] > 0
    assert measurements[1]["measurement"]["unit"] == "m"

    # Polygon: area
    assert measurements[2]["geometry_type"] == "Polygon"
    assert measurements[2]["measurement"]["type"] == "area"
    assert measurements[2]["measurement"]["value"] > 0
    assert measurements[2]["measurement"]["unit"] == "m²"


def test_get_file_measurements_not_found(client: TestClient):
    random_id = uuid.uuid4()
    response = client.get(f"/api/files/{random_id}/measurements/")
    assert response.status_code == 404
