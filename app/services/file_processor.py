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


def process_file(file_path: str) -> gpd.GeoDataFrame:
    """
    Process a supported geospatial file.

    Supported formats:
    - KML
    - ZIP containing a Shapefile
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Provided path is not a file: {file_path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    if extension == ".kml":
        return _read_kml(path)

    if extension == ".zip":
        return _read_shapefile_zip(path)

    raise ValueError(
        f"Unsupported file format: {extension}"
    )


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
        raise ValueError(
            f"Unable to read KML file: {exc}"
        ) from exc

    if gdf.empty:
        raise ValueError(
            "KML file does not contain any features."
        )

    return gdf


def _read_shapefile_zip(path: Path) -> gpd.GeoDataFrame:
    """
    Read a ZIP archive containing a Shapefile.

    A Shapefile requires at minimum:
    .shp
    .shx
    .dbf
    """

    try:
        with zipfile.ZipFile(path, "r") as archive:

            if archive.testzip() is not None:
                raise ValueError(
                    "ZIP archive is corrupted."
                )

            members = archive.namelist()

            shapefile_members = [
                member
                for member in members
                if member.lower().endswith(".shp")
            ]

            if not shapefile_members:
                raise ValueError(
                    "ZIP archive does not contain a Shapefile (.shp)."
                )

            shapefile_member = shapefile_members[0]

            shapefile_path_in_zip = Path(
                shapefile_member
            )

            base_name = shapefile_path_in_zip.stem
            parent_directory = shapefile_path_in_zip.parent

            required_files = {
                f"{base_name}{extension}".lower()
                for extension in REQUIRED_SHAPEFILE_EXTENSIONS
            }

            available_files = {
                Path(member).name.lower()
                for member in members
                if Path(member).parent == parent_directory
            }

            missing_files = required_files - available_files

            if missing_files:
                raise ValueError(
                    "Shapefile is incomplete. "
                    f"Missing files: {sorted(missing_files)}"
                )

            with tempfile.TemporaryDirectory() as temp_dir:

                archive.extractall(temp_dir)

                shapefile_path = (
                    Path(temp_dir)
                    / shapefile_member
                )

                try:
                    gdf = gpd.read_file(
                        shapefile_path
                    )
                except Exception as exc:
                    raise ValueError(
                        f"Unable to read Shapefile: {exc}"
                    ) from exc

                if gdf.empty:
                    raise ValueError(
                        "Shapefile does not contain any features."
                    )

                return gdf

    except zipfile.BadZipFile as exc:
        raise ValueError(
            "The uploaded file is not a valid ZIP archive."
        ) from exc