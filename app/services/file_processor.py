from pathlib import Path
import tempfile
import zipfile

import geopandas as gpd

SUPPORTED_EXTENSIONS = {".kml", ".zip"}

REQUIRED_SHAPEFILE_EXTENSIONS = {
    ".shp",
    ".shx",
    ".dbf",
}

# Limits for ZIP security (Zip Bomb / Resource exhaustion protection)
MAX_ZIP_ENTRIES = 500
MAX_UNCOMPRESSED_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB


def process_file(file_path: str) -> gpd.GeoDataFrame:
    """
    Process a supported geospatial file.

    Supported formats:
    - KML (.kml)
    - ZIP containing a Shapefile (.zip)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Provided path is not a file: {file_path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{extension}'. Only .kml and .zip are supported."
        )

    if extension == ".kml":
        return _read_kml(path)

    if extension == ".zip":
        return _read_shapefile_zip(path)

    raise ValueError(f"Unsupported file format: {extension}")


def _read_kml(path: Path) -> gpd.GeoDataFrame:
    """
    Read a KML file using GeoPandas.
    """
    try:
        gdf = gpd.read_file(
            path,
            driver="KML",
        )
    except Exception as exc:
        raise ValueError(f"Unable to read KML file: {exc}") from exc

    if gdf.empty:
        raise ValueError("KML file does not contain any features.")

    return gdf


def _read_shapefile_zip(path: Path) -> gpd.GeoDataFrame:
    """
    Read a ZIP archive containing a Shapefile with strict security validation.
    Prevents Zip Slip (path traversal attacks) and resource exhaustion.

    A Shapefile requires at minimum:
    .shp, .shx, .dbf (with optional .prj and others).
    """
    try:
        with zipfile.ZipFile(path, "r") as archive:
            # Check for corrupt archive
            if archive.testzip() is not None:
                raise ValueError("ZIP archive is corrupted.")

            infolist = archive.infolist()

            # Protect against excessive number of entries
            if len(infolist) > MAX_ZIP_ENTRIES:
                raise ValueError(
                    f"ZIP archive contains too many entries (max {MAX_ZIP_ENTRIES})."
                )

            # Protect against uncompressed size bomb
            total_uncompressed_size = sum(info.file_size for info in infolist)
            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE_BYTES:
                raise ValueError(
                    "ZIP archive uncompressed size exceeds allowable limits (200MB)."
                )

            # Detect Shapefile members
            shapefile_members = [
                info.filename
                for info in infolist
                if info.filename.lower().endswith(".shp")
            ]

            if not shapefile_members:
                raise ValueError(
                    "ZIP archive does not contain a Shapefile (.shp)."
                )

            # Protect against path traversal (Zip Slip)
            for info in infolist:
                filename = info.filename
                if (
                    filename.startswith("/")
                    or filename.startswith("\\")
                    or ".." in Path(filename).parts
                ):
                    raise ValueError(
                        f"Insecure ZIP archive: path traversal detected in '{filename}'."
                    )

            primary_shp = shapefile_members[0]
            shp_path_in_zip = Path(primary_shp)
            base_name = shp_path_in_zip.stem
            parent_dir = shp_path_in_zip.parent

            required_files = {
                f"{base_name}{ext}".lower()
                for ext in REQUIRED_SHAPEFILE_EXTENSIONS
            }

            available_files = {
                Path(info.filename).name.lower()
                for info in infolist
                if Path(info.filename).parent == parent_dir
            }

            missing_files = required_files - available_files
            if missing_files:
                raise ValueError(
                    f"Shapefile is incomplete. Missing files: {sorted(missing_files)}"
                )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir).resolve()

                for info in infolist:
                    dest_path = (temp_dir_path / info.filename).resolve()
                    if not dest_path.is_relative_to(temp_dir_path):
                        raise ValueError(
                            "Insecure ZIP archive: extracted path escapes target directory."
                        )
                    archive.extract(info, temp_dir_path)

                full_shp_path = temp_dir_path / primary_shp

                try:
                    gdf = gpd.read_file(full_shp_path)
                except Exception as exc:
                    raise ValueError(f"Unable to read Shapefile: {exc}") from exc

                if gdf.empty:
                    raise ValueError("Shapefile does not contain any features.")

                return gdf

    except zipfile.BadZipFile as exc:
        raise ValueError("The uploaded file is not a valid ZIP archive.") from exc