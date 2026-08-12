import json
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




    def write_data(self, generate_id=True):
        """Write data to the JSON file.

        Args:
            generate_id (bool):
                If True, generate a unique script ID and use it as
                the key for the stored JSON object.
        """

        if self.data is None:
            return "Provide the dictionary data to the class while initializing"

        payload = self.data

        # Read existing data
        if self.json_file.stat().st_size > 0:
            try:
                with open(self.json_file, mode="r", encoding="utf-8") as json_file_reader:
                    existing_data = json.load(json_file_reader)
            except json.JSONDecodeError:
                existing_data = {}
        else:
            existing_data = {}

        # Make sure the root structure is a dictionary
        if not isinstance(existing_data, dict):
            existing_data = {}

        if generate_id:
            script_id = str(uuid4())

            # Store the entire payload under the ID
            existing_data[script_id] = payload

        else:
            # If no ID is generated, merge/write payload normally
            existing_data.update(payload)

        # Write everything back
        with open(self.json_file, mode="w", encoding="utf-8") as file_writer:
            json.dump(
                existing_data,
                file_writer,
                indent=4,
                ensure_ascii=False
            )

        return True

    def read_response(self, fetch_script_ids = True):

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


read = SaveLlmResponse()
res = read.read_response()
print(type(res))



        
