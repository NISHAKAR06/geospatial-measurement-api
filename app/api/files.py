import logging
from pathlib import Path
import tempfile
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.file import File as FileModel
from app.models.feature import Feature as FeatureModel
from app.schemas.file import (
    FeatureMeasurementResponse,
    FileResponse,
    MeasurementDetail,
    MeasurementListResponse,
)
from app.services.file_processor import process_file
from app.services.measurement import calculate_measurements, geometry_to_geojson
from app.services.persistence import persist_processed_dataset

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/files",
    tags=["Files"],
)

ALLOWED_EXTENSIONS = {".kml", ".zip"}


@router.post(
    "/",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process geospatial file",
)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    db: Session = Depends(get_db),
):
    """
    Upload a KML (.kml) or Shapefile ZIP archive (.zip),
    extract features, reproject to an optimal metric CRS, compute measurements,
    and persist results.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .kml and .zip files are supported.",
        )

    # Read and enforce max upload size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    temp_file_path = None

    try:
        total_size = 0
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=(
                            f"File size exceeds the maximum limit of "
                            f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                        ),
                    )
                temp_file.write(chunk)

        # Process geospatial features
        gdf = process_file(temp_file_path)

        # Compute CRS and accurate metric measurements
        measurements, original_crs, measurement_crs = calculate_measurements(gdf)

        # Persist to database
        file_record = persist_processed_dataset(
            db=db,
            filename=file.filename,
            original_gdf=gdf,
            measurement_results=measurements,
            original_crs=original_crs,
            measurement_crs=measurement_crs,
        )

        return file_record

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as exc:
        logger.warning(f"Validation failure for file '{file.filename}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.error(f"Unexpected error processing '{file.filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the geospatial file.",
        ) from exc

    finally:
        if temp_file_path:
            try:
                Path(temp_file_path).unlink(missing_ok=True)
            except Exception:
                pass


@router.get(
    "/{id}/",
    response_model=FileResponse,
    summary="Get file details",
)
def get_file_details(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve metadata for a previously uploaded and processed file.
    """
    file_record = db.query(FileModel).filter(FileModel.id == id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{id}' was not found.",
        )
    return file_record


@router.get(
    "/{id}/measurements/",
    response_model=MeasurementListResponse,
    summary="Get file measurements",
)
def get_file_measurements(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve extracted features, GeoJSON geometries, and computed spatial measurements for a file.
    """
    file_record = db.query(FileModel).filter(FileModel.id == id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{id}' was not found.",
        )

    features = (
        db.query(FeatureModel)
        .filter(FeatureModel.file_id == id)
        .order_by(FeatureModel.feature_index.asc())
        .all()
    )

    measurement_responses = []
    for feat in features:
        # Construct measurement detail
        measurement_detail = None
        if feat.measurement_type is not None or feat.status not in (None, "OK"):
            measurement_detail = MeasurementDetail(
                type=feat.measurement_type,
                value=feat.measurement_value,
                unit=feat.measurement_unit,
                status=feat.status or "OK",
            )
        elif feat.geometry_type in ("Point", "MultiPoint"):
            measurement_detail = None

        # Convert stored spatial geometry into clean GeoJSON mapping
        geojson_geom = geometry_to_geojson(feat.geometry)

        measurement_responses.append(
            FeatureMeasurementResponse(
                feature_id=feat.feature_index,
                geometry_type=feat.geometry_type,
                geometry=geojson_geom,
                crs=file_record.original_crs,
                measurement=measurement_detail,
                properties=feat.properties or {},
            )
        )

    return MeasurementListResponse(
        file_id=file_record.id,
        original_crs=file_record.original_crs,
        measurement_crs=file_record.measurement_crs,
        measurements=measurement_responses,
    )