import json
from pathlib import Path


class SaveLlmResponse:
    def __init__(self, data = None, directory: str = 'data', filename: str = 'llm_response.json'):
        
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.project_root / directory

        # Always ensure the full directory tree exists (handles nested paths too)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.json_file = self.data_dir / filename

        # Ensure any subdirectory within filename (e.g. "scene/props.json") is created
        self.json_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.json_file.exists():
            self.json_file.touch()

        self.data = data

    def write_data(self):

        if self.data is None:
            return f'Provide the dictionary data to the class while initializing'

        # write to the llm_response file
        with open(self.json_file, mode='w', encoding='utf-8') as file_writer:
            json.dump(self.data, file_writer, indent=4)

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
        return data




        
