from pathlib import Path
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.file_processor import process_file
from app.services.measurement import calculate_measurements


router = APIRouter(
    prefix="/api/files",
    tags=["Files"],
)


ALLOWED_EXTENSIONS = {".kml", ".zip"}


@router.post("/")
async def upload_file(
    file: UploadFile = File(...)
):
    """
    Upload a KML or Shapefile ZIP,
    process its features, and calculate measurements.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Only .kml and .zip files are supported."
            ),
        )

    temp_file_path = None

    try:
        file_content = await file.read()

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:

            temp_file.write(file_content)
            temp_file_path = temp_file.name

        gdf = process_file(temp_file_path)

        measurements = calculate_measurements(gdf)

        return {
            "filename": file.filename,
            "crs": str(gdf.crs),
            "feature_count": len(gdf),
            "measurements": measurements,
        }

    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process file: {exc}",
        ) from exc

    finally:
        if temp_file_path:
            Path(temp_file_path).unlink(
                missing_ok=True
            )