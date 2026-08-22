import json
import shutil
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4


class FileManipulator:
    """
    Centralized file manipulation class for handling path resolution,
    JSON reading/writing, text operations, directory creation/cleanup,
    file copying, and LLM response persistence.
    """

    def __init__(self, data: Any = None, directory: str = 'data', filename: str = 'llm_response.json'):
        self.project_root = FileManipulator.get_project_root()
        self.data_dir = FileManipulator.ensure_dir(self.project_root / directory)
        self.json_file = self.data_dir / filename
        FileManipulator.ensure_dir(self.json_file.parent)

        if not self.json_file.exists():
            self.json_file.touch()

        self.current_id = None
        self.data = data

    @staticmethod
    def get_project_root() -> Path:
        """Returns the project root directory (yt-agent)."""
        return Path(__file__).resolve().parents[2]

    @classmethod
    def resolve_path(cls, filename: Union[str, Path], directory: str = 'data') -> Path:
        """Resolves a file or directory path relative to project root or specified directory."""
        project_root = cls.get_project_root()
        path = Path(filename)
        if path.is_absolute():
            return path
        if directory:
            return project_root / directory / path
        return project_root / path

    @classmethod
    def resolve_video_path(cls, filename: str = 'video.mp4', directory: str = 'data') -> Path:
        """Resolves path for a video file."""
        return cls.resolve_path(filename=filename, directory=directory)

    @staticmethod
    def ensure_dir(dir_path: Union[str, Path]) -> Path:
        """Ensures that a directory (and any parent directories) exists."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def generate_readable_run_id(topic: str = "") -> str:
        """Generates a human-readable run ID using current timestamp and optional topic slug."""
        from datetime import datetime, timezone
        import re

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if topic:
            slug = re.sub(r"[^\w\s-]", "", topic.lower())
            slug = re.sub(r"[\s-]+", "_", slug).strip("_")[:30]
        else:
            slug = ""

        return f"{timestamp}_{slug}" if slug else timestamp

    @staticmethod
    def create_run_directory(run_id: Optional[str] = None, topic: str = "") -> tuple[str, Path]:
        """Creates a unique run directory in data/runs/<run_id>."""
        if not run_id:
            run_id = FileManipulator.generate_readable_run_id(topic)
        run_dir = FileManipulator.get_project_root() / "data" / "runs" / run_id
        FileManipulator.ensure_dir(run_dir)
        return run_id, run_dir

    @staticmethod
    def write_json(file_path: Union[str, Path], data: Any, indent: int = 2, ensure_ascii: bool = False) -> Path:
        """Writes dictionary or serializable data to a JSON file."""
        path = Path(file_path)
        FileManipulator.ensure_dir(path.parent)
        path.write_text(json.dumps(data, indent=indent, ensure_ascii=ensure_ascii), encoding="utf-8")
        return path

    @staticmethod
    def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """Reads and parses a JSON file. Returns `default` if file does not exist or is invalid."""
        path = Path(file_path)
        if not path.exists():
            return default
        try:
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return default
            return json.loads(content)
        except (json.JSONDecodeError, TypeError, OSError):
            return default

    @staticmethod
    def write_text(file_path: Union[str, Path], text: str, encoding: str = "utf-8") -> Path:
        """Writes text content to a file."""
        path = Path(file_path)
        FileManipulator.ensure_dir(path.parent)
        path.write_text(text, encoding=encoding)
        return path

    @staticmethod
    def read_text(file_path: Union[str, Path], default: str = "", encoding: str = "utf-8") -> str:
        """Reads text content from a file."""
        path = Path(file_path)
        if not path.exists():
            return default
        try:
            return path.read_text(encoding=encoding)
        except OSError:
            return default

    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path], overwrite: bool = True) -> Path:
        """Copies a file from source to destination."""
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        dest = Path(destination)
        FileManipulator.ensure_dir(dest.parent)
        if dest.exists() and not overwrite:
            return dest
        shutil.copy2(src, dest)
        return dest

    @classmethod
    def copy_file_to_data(cls, source_path: Union[str, Path], destination_filename: str = 'video.mp4', directory: str = 'data') -> Path:
        """Copies a file to the data directory."""
        destination = cls.resolve_path(filename=destination_filename, directory=directory)
        return cls.copy_file(source_path, destination)

    @staticmethod
    def copy_directory(source_dir: Union[str, Path], destination_dir: Union[str, Path], overwrite: bool = True) -> Path:
        """Copies a directory recursively."""
        src = Path(source_dir)
        if not src.exists():
            raise FileNotFoundError(f"Source directory not found: {src}")
        dest = Path(destination_dir)
        FileManipulator.ensure_dir(dest.parent)
        shutil.copytree(src, dest, dirs_exist_ok=overwrite)
        return dest

    @staticmethod
    def delete_file(file_path: Union[str, Path], missing_ok: bool = True) -> bool:
        """Deletes a file safely."""
        path = Path(file_path)
        try:
            path.unlink(missing_ok=missing_ok)
            return True
        except OSError:
            return False

    @staticmethod
    def delete_directory(dir_path: Union[str, Path], missing_ok: bool = True) -> bool:
        """Deletes a directory recursively."""
        path = Path(dir_path)
        if not path.exists():
            return missing_ok
        try:
            shutil.rmtree(path)
            return True
        except OSError:
            return False

    @staticmethod
    def clean_directory(dir_path: Union[str, Path]) -> None:
        """Removes all contents of a directory without deleting the directory itself."""
        path = Path(dir_path)
        if not path.exists():
            FileManipulator.ensure_dir(path)
            return
        for item in path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink(missing_ok=True)

    @staticmethod
    def exists(path: Union[str, Path]) -> bool:
        """Checks if a file or directory exists."""
        return Path(path).exists()

    @staticmethod
    def file_exists(path: Union[str, Path]) -> bool:
        """Checks if path exists and is a file."""
        return Path(path).is_file()

    @staticmethod
    def dir_exists(path: Union[str, Path]) -> bool:
        """Checks if path exists and is a directory."""
        return Path(path).is_dir()

    # --- LLM Response handling methods ---

    def write_data(self, generate_id: bool = True) -> Optional[str]:
        """Write payload data to the JSON file, appending unique script_id if requested."""
        if self.data is None:
            return "Provide the dictionary data to the class while initializing"

        payload = self.data

        if isinstance(payload, dict) and generate_id:
            self.current_id = str(uuid4())
            payload = {self.current_id: payload}

        existing_data = FileManipulator.read_json(self.json_file, default={})
        if not isinstance(existing_data, dict):
            existing_data = {}

        existing_data.update(payload)
        FileManipulator.write_json(self.json_file, existing_data, indent=4, ensure_ascii=False)

        return self.current_id

    def read_response(self) -> Any:
        """Read latest or specific LLM response from json_file."""
        data = FileManipulator.read_json(self.json_file, default=None)
        if not data:
            return 'No data found'

        if isinstance(data, list):
            return data[-1] if data else 'No data found'

        if not isinstance(data, dict):
            return 'No data found'

        if self.current_id is None:
            last_key = list(data.keys())[-1]
            return data[last_key]

        return data.get(self.current_id, 'No data found')

    def read_response_with_id(self) -> tuple[Optional[str], Any]:
        """Read the latest response and return (script_id, data) tuple."""
        data = FileManipulator.read_json(self.json_file, default=None)
        if not data or not isinstance(data, dict):
            return None, 'No data found'

        if self.current_id and self.current_id in data:
            return self.current_id, data[self.current_id]

        last_key = list(data.keys())[-1]
        return last_key, data[last_key]


# Maintain SaveLlmResponse alias pointing to FileManipulator for backwards compatibility
SaveLlmResponse = FileManipulator
