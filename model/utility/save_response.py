import json
import shutil
from pathlib import Path


class SaveLlmResponse:
    def __init__(self, data = None):
        
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.project_root/'data'

        if not self.data_dir.exists():

            # create the directory if it does'nt exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

        self.json_file = self.data_dir / 'llm_response.json'

        if self.json_file.exists() and self.json_file.is_dir():
            shutil.rmtree(self.json_file)

        if not self.json_file.exists():
            self.json_file.touch(exist_ok=True)

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




        
