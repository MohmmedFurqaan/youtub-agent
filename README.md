# YouTube Agent

This project is a notebook-based AI workflow for generating YouTube-style video prompts and related content. It uses Python, Jupyter, and several AI libraries, including LangChain and OpenRouter.

## Requirements

- Python 3.12+
- uv installed on your machine

## Setup

1. Clone the repository and move into the project folder.
2. Create the environment and install dependencies:

```bash
uv sync
```

3. Copy the example environment file and fill in your API key:

```bash
cp .env.example .env
```

Then edit `.env` and set at least:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

You can also customize the system prompt in `.env` with `SYSTEM_VIDEO_PROMPT`.

## Run the project

Start Jupyter Lab:

```bash
jupyter lab
```

Then open the notebook file:

- `main.ipynb`

Run the notebook cells in order from the top.

## Project structure

- `main.ipynb` - main notebook entry point
- `model/utility/` - supporting agent and prompt logic
- `.env` - local environment variables (not committed)

## Notes

- If you are using a fresh environment, make sure the dependencies are installed before opening the notebook.
- If Jupyter does not detect the environment automatically, restart it after running `uv sync`.
