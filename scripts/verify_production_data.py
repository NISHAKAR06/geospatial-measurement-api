from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# SQLite dialect patch for offline verification
from geoalchemy2.admin.dialects import sqlite
sqlite.after_create = lambda *args, **kwargs: None
sqlite.before_create = lambda *args, **kwargs: None
sqlite.after_drop = lambda *args, **kwargs: None
sqlite.before_drop = lambda *args, **kwargs: None

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models

# In-memory test engine
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = TestingSessionLocal()

def override_get_db():
    yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
prod_dir = Path("sample_data/production")

files_to_test = [
    ("drone_solar_farm_survey.kml", "application/vnd.google-earth.kml+xml"),
    ("infrastructure_transmission_lines_wgs84.zip", "application/zip"),
    ("cadastral_parcels_utm43n.zip", "application/zip"),
    ("gas_pipeline_corridor_feet.zip", "application/zip"),
    ("ground_control_points_wgs84.zip", "application/zip"),
]

print("=== Verifying Production Datasets Against API Endpoints ===")

for fname, mime in files_to_test:
    fpath = prod_dir / fname
    assert fpath.exists(), f"Missing file {fpath}"
    with open(fpath, "rb") as f:
        res = client.post("/api/files/", files={"file": (fname, f.read(), mime)})
    assert res.status_code == 201, f"Upload failed for {fname}: {res.text}"
    data = res.json()
    file_id = data["id"]
    count = data["feature_count"]

    # Verify GET /api/files/{id}/
    file_res = client.get(f"/api/files/{file_id}/")
    assert file_res.status_code == 200

    # Verify GET /api/files/{id}/measurements/
    m_res = client.get(f"/api/files/{file_id}/measurements/")
    assert m_res.status_code == 200
    m_data = m_res.json()

    orig_crs = m_data.get("original_crs")
    meas_crs = m_data.get("measurement_crs")
    meas_list = m_data.get("measurements", [])

    print(f"\n[OK] File: {fname}")
    print(f"     Features Count: {count}")
    print(f"     Original CRS:   {orig_crs}")
    print(f"     Measurement CRS: {meas_crs}")
    for idx, item in enumerate(meas_list[:3]):
        geom_type = item.get("geometry_type")
        meas = item.get("measurement")
        if meas:
            print(f"     - Feature {idx} ({geom_type}): {meas['type']} = {meas['value']} {meas['unit']}")
        else:
            print(f"     - Feature {idx} ({geom_type}): No measurement (Point / MultiPoint)")

print("\n=== All Production Datasets Passed API Verification Successfully ===")
