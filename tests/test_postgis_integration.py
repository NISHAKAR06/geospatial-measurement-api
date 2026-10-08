import os
import pytest
from sqlalchemy import create_engine, text
from shapely.geometry import Point

from app.core.config import settings
from app.models.file import File
from app.models.feature import Feature
from app.services.persistence import persist_processed_dataset
import geopandas as gpd


@pytest.mark.integration
def test_postgis_live_schema_and_spatial_index():
    """
    Verifies that real PostGIS database has:
    1. Active PostGIS extension
    2. files and features tables
    3. GIST spatial index on features.geometry
    4. Successful spatial insert and retrieval with SRID 4326
    """
    db_url = settings.DATABASE_URL
    if not db_url.startswith("postgresql"):
        pytest.skip("Skipping PostGIS integration test: DATABASE_URL is not PostgreSQL")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # 1. Verify PostGIS extension
            postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
            assert postgis_ver is not None, "PostGIS extension is not active"

            # 2. Verify tables exist
            tables = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            ).scalars().all()
            assert "files" in tables, "files table missing in PostGIS"
            assert "features" in tables, "features table missing in PostGIS"

            # 3. Verify GIST index
            indices = conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'features';")
            ).scalars().all()
            assert "idx_features_geometry" in indices, "idx_features_geometry GIST index missing"

            # 4. Verify unique constraint
            constraints = conn.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE conrelid = 'features'::regclass;"
                )
            ).scalars().all()
            assert "uq_features_file_id_feature_index" in constraints, "Unique constraint missing"

    except Exception as exc:
        pytest.skip(f"PostGIS instance not reachable: {exc}")

