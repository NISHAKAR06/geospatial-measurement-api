import uuid
from typing import Any, Dict, List
import geopandas as gpd
from shapely import force_2d
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape

from app.models.file import File
from app.models.feature import Feature


def persist_processed_dataset(
    db: Session,
    filename: str,
    original_gdf: gpd.GeoDataFrame,
    measurement_results: List[Dict[str, Any]],
    original_crs: str,
    measurement_crs: str,
) -> File:
    """
    Persist file metadata and extracted spatial features into the database.
    Operates within a database transaction.
    """
    try:
        # Prepare WGS84 geometries for standardized PostGIS storage (SRID 4326)
        if original_gdf.crs is not None and original_gdf.crs.to_epsg() != 4326:
            storage_gdf = original_gdf.to_crs(4326)
        else:
            storage_gdf = original_gdf

        file_id = uuid.uuid4()
        file_record = File(
            id=file_id,
            filename=filename,
            original_crs=original_crs,
            measurement_crs=measurement_crs,
            feature_count=len(measurement_results),
            status="COMPLETED",
        )
        db.add(file_record)
        db.flush()

        geom_col = storage_gdf.geometry.name
        is_sqlite = db.bind is not None and db.bind.dialect.name == "sqlite"

        feature_records = []
        for item in measurement_results:
            idx = item["feature_id"]
            geom = storage_gdf.geometry.iloc[idx] if idx < len(storage_gdf) else None

            # Spatial geometry representation: from_shape for PostGIS, WKB for SQLite
            postgis_geom = None
            if geom is not None and not geom.is_empty:
                try:
                    if getattr(geom, "has_z", False):
                        geom = force_2d(geom)
                    if is_sqlite:
                        postgis_geom = geom.wkb
                    else:
                        postgis_geom = from_shape(geom, srid=4326)
                except Exception:
                    postgis_geom = None

            measurement = item.get("measurement")
            m_type = measurement.get("type") if measurement else None
            m_val = measurement.get("value") if measurement else None
            m_unit = measurement.get("unit") if measurement else None
            m_status = (
                measurement.get("status")
                if measurement
                else ("OK" if item.get("geometry_type") in ("Point", "MultiPoint") else None)
            )

            feat = Feature(
                file_id=file_id,
                feature_index=idx,
                geometry_type=item.get("geometry_type"),
                properties=item.get("properties") or {},
                measurement_type=m_type,
                measurement_value=m_val,
                measurement_unit=m_unit,
                status=m_status,
                geometry=postgis_geom,
            )
            feature_records.append(feat)

        db.add_all(feature_records)
        db.commit()
        db.refresh(file_record)
        return file_record

    except Exception:
        db.rollback()
        raise

