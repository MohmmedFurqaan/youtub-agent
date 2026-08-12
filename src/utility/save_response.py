import json
import shutil
from pathlib import Path
from uuid import uuid4


class SaveLlmResponse:
    def __init__(self, data=None, directory: str = 'data', filename: str = 'llm_response.json'):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / directory
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.json_file = self.data_dir / filename
        self.json_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.json_file.exists():
            self.json_file.touch()

        self.data = data

    @classmethod
    def resolve_path(cls, filename: str, directory: str = 'data') -> Path:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / directory / filename

    @classmethod
    def resolve_video_path(cls, filename: str = 'video.mp4', directory: str = 'data') -> Path:
        return cls.resolve_path(filename=filename, directory=directory)

    @staticmethod
    def copy_file_to_data(source_path, destination_filename: str = 'video.mp4', directory: str = 'data') -> Path:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        destination = SaveLlmResponse.resolve_path(filename=destination_filename, directory=directory)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    def write_data(self, generate_id=True):
        """Write dict/list data to the JSON file.

        Args:
            generate_id (bool):
                If True and the payload is a dict, append a unique script_id field.
        """
        if self.data is None:
            return "Provide the dictionary data to the class while initializing"

        payload = self.data

        if isinstance(payload, dict) and generate_id:
            payload = {**payload, 'script_id': str(uuid4())}

        if self.json_file.stat().st_size > 0:
            try:
                with open(self.json_file, mode='r', encoding='utf-8') as json_file_reader:
                    existing_data = json.load(json_file_reader)
            except json.JSONDecodeError:
                existing_data = {}
        else:
            existing_data = {}

        if isinstance(existing_data, list):
            existing_data.append(payload)
            to_write = existing_data
        else:
            if isinstance(payload, dict):
                if not isinstance(existing_data, dict):
                    existing_data = {}
                existing_data.update(payload)
                to_write = existing_data
            else:
                to_write = payload

        with open(self.json_file, mode='w', encoding='utf-8') as file_writer:
            json.dump(to_write, file_writer, indent=4, ensure_ascii=False)

        return True

    def read_response(self):
        if not self.json_file.exists():
            return {}

        with open(self.json_file, 'r', encoding='utf-8') as file_reader:
            raw_data = file_reader.read()

        if not raw_data.strip():
            return 'No data found'

        try:
            data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            return 'No data found'

        if not data:
            return 'No data found'

        if isinstance(data, list):
            return data[-1] if data else 'No data found'

        return data

