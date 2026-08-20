import os
import tempfile
from pathlib import Path

import pytest
from src.utility.file_manipuator import FileManipulator, SaveLlmResponse


def test_get_project_root():
    root = FileManipulator.get_project_root()
    assert isinstance(root, Path)
    assert (root / "src").exists()


def test_resolve_path():
    p = FileManipulator.resolve_path("test.json", directory="data")
    assert p == FileManipulator.get_project_root() / "data" / "test.json"

    abs_p = Path("/tmp/absolute.txt").resolve()
    assert FileManipulator.resolve_path(abs_p) == abs_p


def test_ensure_dir(tmp_path):
    sub = tmp_path / "a" / "b" / "c"
    created = FileManipulator.ensure_dir(sub)
    assert created.exists()
    assert created.is_dir()


def test_create_run_directory():
    run_id, run_dir = FileManipulator.create_run_directory()
    assert isinstance(run_id, str)
    assert len(run_id) > 0
    assert run_dir.exists()
    assert run_dir.name == run_id
    # Clean up test run directory
    FileManipulator.delete_directory(run_dir)


def test_json_read_write(tmp_path):
    json_path = tmp_path / "data.json"
    payload = {"name": "yt-agent", "active": True, "count": 42}

    written_path = FileManipulator.write_json(json_path, payload, indent=2)
    assert written_path.exists()

    read_data = FileManipulator.read_json(json_path)
    assert read_data == payload

    # Test non-existent file
    assert FileManipulator.read_json(tmp_path / "missing.json", default={"fallback": 1}) == {"fallback": 1}

    # Test corrupt JSON
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("invalid json {", encoding="utf-8")
    assert FileManipulator.read_json(corrupt_file, default=None) is None


def test_text_read_write(tmp_path):
    text_path = tmp_path / "sub" / "hello.txt"
    content = "Hello, FileManipulator!"

    written = FileManipulator.write_text(text_path, content)
    assert written.exists()

    read_val = FileManipulator.read_text(text_path)
    assert read_val == content

    assert FileManipulator.read_text(tmp_path / "nonexistent.txt", default="default") == "default"


def test_copy_file_and_directory(tmp_path):
    src_file = tmp_path / "src.txt"
    FileManipulator.write_text(src_file, "Source content")

    dest_file = tmp_path / "dst" / "copied.txt"
    copied = FileManipulator.copy_file(src_file, dest_file)
    assert copied.exists()
    assert FileManipulator.read_text(copied) == "Source content"

    # Test directory copying
    src_dir = tmp_path / "dir_src"
    FileManipulator.write_text(src_dir / "f1.txt", "F1")
    FileManipulator.write_text(src_dir / "sub" / "f2.txt", "F2")

    dest_dir = tmp_path / "dir_dst"
    FileManipulator.copy_directory(src_dir, dest_dir)
    assert (dest_dir / "f1.txt").exists()
    assert (dest_dir / "sub" / "f2.txt").exists()


def test_delete_and_clean_directory(tmp_path):
    dir_to_clean = tmp_path / "clean_me"
    FileManipulator.write_text(dir_to_clean / "file1.txt", "1")
    FileManipulator.write_text(dir_to_clean / "sub" / "file2.txt", "2")

    FileManipulator.clean_directory(dir_to_clean)
    assert dir_to_clean.exists()
    assert len(list(dir_to_clean.iterdir())) == 0

    file_to_del = tmp_path / "to_delete.txt"
    FileManipulator.write_text(file_to_del, "del")
    assert FileManipulator.delete_file(file_to_del)
    assert not file_to_del.exists()

    dir_to_del = tmp_path / "del_dir"
    FileManipulator.ensure_dir(dir_to_del)
    assert FileManipulator.delete_directory(dir_to_del)
    assert not dir_to_del.exists()


def test_existence_helpers(tmp_path):
    f = tmp_path / "test.txt"
    d = tmp_path / "test_dir"
    FileManipulator.write_text(f, "data")
    FileManipulator.ensure_dir(d)

    assert FileManipulator.exists(f)
    assert FileManipulator.exists(d)
    assert FileManipulator.file_exists(f)
    assert not FileManipulator.file_exists(d)
    assert FileManipulator.dir_exists(d)
    assert not FileManipulator.dir_exists(f)


def test_save_llm_response(tmp_path):
    # Test SaveLlmResponse alias and write_data / read_response functionality
    data_payload = {"topic": "API request", "scenes": 5}
    saver = SaveLlmResponse(data=data_payload, directory=str(tmp_path), filename="llm_resp.json")
    generated_id = saver.write_data(generate_id=True)
    assert generated_id is not None

    read_back = saver.read_response()
    assert read_back == data_payload

    script_id, resp_data = saver.read_response_with_id()
    assert script_id == generated_id
    assert resp_data == data_payload
