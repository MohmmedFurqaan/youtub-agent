# YouTube Agent

This project is a notebook-based AI workflow for generating YouTube-style video prompts and related content. It uses Python, Jupyter, and several AI libraries, including LangChain and OpenRouter.

## How to get started with development

1. Clone the repository
```bash
git clone https://github.com/MohmmedFurqaan/youtub-agent.git
```

- change directory
```bash 
cd youtube-agent
```

2. Checkout from the Main branch (most imortant)
```bash
git checkout feature/yt-video
```

3. start developing the feature and push the code to the branch 
```bash
git status
git add . # add all the local changes
git commit -m"{add your message about the feature}"
git push origin feature/yt-video # push to the github
```

4. (Optional) if you have any issue follow the give step
- open the github
- open the repostiry of the `youtub-agent`
- head to the **Issues** section
- rais the issues in the branch by siply **create issue**

---

## Requirements

- Python 3.12+
- uv installed on your machine 
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

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

Start run the command:

```bash
uv run main.py
```

Then open the python file:

- `main.py`

Run the notebook cells in order from the top.

## Project structure

- `main.py` - main notebook entry point
- `model/service/` - supporting agent and prompt logic
- `.env` - local environment variables (not committed)

## Notes

- If you are using a fresh environment, make sure the dependencies are installed before opening the notebook.
- If Jupyter does not detect the environment automatically, restart it after running `uv sync`.
