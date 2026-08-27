from io import BytesIO

import pytest

from flaxon.files import FileStorage
from flaxon.files.upload import UploadedFile


def test_file_storage_rejects_paths_outside_root(tmp_path):
    storage = FileStorage(str(tmp_path / "uploads"))
    upload = UploadedFile("note.txt", "text/plain", 4, BytesIO(b"test"))
    with pytest.raises(ValueError):
        storage.save(upload, path="../outside")
    assert storage.exists(str(tmp_path / "outside.txt")) is False


def test_file_storage_allows_nested_paths(tmp_path):
    storage = FileStorage(str(tmp_path / "uploads"))
    upload = UploadedFile("note.txt", "text/plain", 4, BytesIO(b"test"))
    path = storage.save(upload, path="documents")
    assert storage.exists(path)
    assert storage.get_file_info(path)["name"].endswith(".txt")
