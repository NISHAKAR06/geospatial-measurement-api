import tempfile
import zipfile
from pathlib import Path
import pytest

from app.services.file_processor import process_file


def test_process_valid_kml():
    kml_path = "sample_data/sample.kml"
    gdf = process_file(kml_path)
    assert not gdf.empty
    assert len(gdf) == 3
    assert gdf.crs is not None


def test_process_valid_shapefile_zip():
    zip_path = "sample_data/sample_shapefile.zip"
    gdf = process_file(zip_path)
    assert not gdf.empty
    assert len(gdf) == 3
    assert gdf.crs is not None


def test_process_unsupported_extension(tmp_path: Path):
    unsupported_file = tmp_path / "test.txt"
    unsupported_file.write_text("Hello world")
    with pytest.raises(ValueError, match="Unsupported file format"):
        process_file(str(unsupported_file))


def test_process_missing_file():
    with pytest.raises(FileNotFoundError, match="File not found"):
        process_file("non_existent_file.kml")


def test_process_corrupt_zip(tmp_path: Path):
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_bytes(b"PK\x03\x04corrupted_data_not_a_valid_zip")
    with pytest.raises(ValueError, match="not a valid ZIP archive|corrupted"):
        process_file(str(corrupt_zip))


def test_process_zip_without_shp(tmp_path: Path):
    zip_path = tmp_path / "no_shp.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "Some text file")
    with pytest.raises(ValueError, match="does not contain a Shapefile"):
        process_file(str(zip_path))


def test_process_incomplete_shapefile(tmp_path: Path):
    zip_path = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("parcel.shp", b"dummy shp")
        # Missing parcel.shx and parcel.dbf
    with pytest.raises(ValueError, match="Shapefile is incomplete"):
        process_file(str(zip_path))


def test_process_zip_path_traversal_attack(tmp_path: Path):
    zip_path = tmp_path / "malicious.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../evil.shp", b"evil content")
        zf.writestr("../evil.shx", b"evil content")
        zf.writestr("../evil.dbf", b"evil content")
    with pytest.raises(ValueError, match="Insecure ZIP archive: path traversal detected"):
        process_file(str(zip_path))

