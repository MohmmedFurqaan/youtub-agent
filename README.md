# YouTube Agent — Faceless Video Generator

This project turns a technical topic into a faceless YouTube-style video pipeline powered by AI, asset generation, and an optional YouTube upload flow.

The current workflow is:

- Phase 1: generate a structured video script with an LLM via OpenRouter
- Phase 2: generate cached media props and scene assets in the project data folder
- Phase 3: render the final MP4 with Remotion
- Optional Phase 4: upload the final MP4 to YouTube using the Google OAuth environment config

---

## Stack

- Python 3.12+
- LangChain + OpenRouter
- Pollinations.ai for background images
- Microsoft edge-tts for narration
- Remotion + React for rendering
- Google YouTube Data API v3 for uploads

---

## Requirements

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | Required for the pipeline |
| uv | latest | Recommended package manager |
| Node.js | 18+ | Only needed for Remotion rendering |
| npm | 9+ | Bundled with Node.js |

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If needed, install it via pip:

```bash
pip install uv
```

---

## Project setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd yt-agent
```

### 2. Install Python dependencies

```bash
uv sync
```

### 3. Install Remotion dependencies

```bash
cd video-renderer
npm install
cd ..
```

### 4. Configure environment variables

Create a `.env` file at the project root and add the required values:

```env
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL_NAME=nvidia/nemotron-3.5-lightning:free
DEVMODE=True

YOUTUBE_CLIENT_ID=your_google_client_id
YOUTUBE_CLIENT_SECRET=your_google_client_secret
YOUTUBE_PROJECT_ID=your_google_project_id

YOUTUBE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
YOUTUBE_TOKEN_URI=https://oauth2.googleapis.com/token
YOUTUBE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
YOUTUBE_REDIRECT_URI=http://localhost
```

Important notes:

- Do not use a local `credentials.json` file.
- The project uses env-based OAuth configuration instead.
- `load_envs.py` validates that the required env vars exist before the pipeline starts.

---

## How the project runs

### Main entry point

```bash
uv run main.py
```

The current main flow does the following:

1. Generate the AI script from the prompt
2. Write the script to `data/llm_response.json`
3. If `DEVMODE` is false, generate media assets and Remotion props
4. If a video exists in the data folder, upload it to YouTube automatically

---

## Script and data storage

The reusable file helper is in [src/utility/save_response.py](src/utility/save_response.py).

It is responsible for:

- resolving project paths under the repo root
- creating directories when needed
- writing JSON payloads to `data/`
- copying a generated video into the data folder for uploads

Default locations:

- `data/llm_response.json` — generated script payload
- `data/metadata/video-props.json` — asset metadata for Remotion
- `data/metadata/scene/` — per-scene background images and audio
- `data/video.mp4` — final uploaded video location if present

---

## YouTube upload flow

The uploader is in [src/youtube/video_uploader.py](src/youtube/video_uploader.py).

It does the following:

- reads OAuth config from `.env`
- creates the YouTube API client without requiring `credentials.json`
- uploads the video passed to it
- defaults to `data/video.mp4` if no path is supplied

Example usage:

```python
from src.youtube.video_uploader import upload_video

upload_video("data/video.mp4", title="My AI Generated Video")
```

The project also wires this into [main.py](main.py), which checks the data folder and uploads automatically when a final MP4 is available.

---

## Rendering

To render the video via Remotion:

```bash
cd video-renderer
npm run render:props
```

Output:

- `video-renderer/out/video.mp4`

Optional preview:

```bash
cd video-renderer
npm run start
```

---

## Repository structure

```text
yt-agent/
├── main.py
├── .env
├── prompts/
│   ├── script_video_prompt.md
│   ├── title_video_prompt.md
│   └── thumbnail_image_prompt.md
├── src/
│   ├── model/
│   │   └── service/
│   │       ├── prompt_agent.py
│   │       └── asset_generator.py
│   ├── utility/
│   │   ├── load_envs.py
│   │   ├── logging_config.py
│   │   └── save_response.py
│   └── youtube/
│       └── video_uploader.py
├── data/
│   ├── llm_response.json
│   ├── video.mp4
│   ├── youtube-dataset/
│   └── metadata/
│       ├── video-props.json
│       └── scene/
├── video-renderer/
├── docs/
├── tests/
└── README.md
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `OPENROUTER_API_KEY is not set` | Add the key to `.env` |
| `OPENROUTER MODEL NAME is not set` | Add `OPENROUTER_MODEL_NAME` to `.env` |
| `No video found in data folder to upload` | Put the final MP4 at `data/video.mp4` |
| Google OAuth fails | Check `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REDIRECT_URI` |
| `uv: command not found` | Install uv and reopen the terminal |
| Remotion render fails | Run `cd video-renderer && npm install` |

---

## Developer notes

- The project prefers centralized file handling through [src/utility/save_response.py](src/utility/save_response.py) instead of random path logic spread across modules.
- You should not add a `credentials.json` file for the YouTube uploader.
- Keep all generated runtime artifacts under `data/` so the pipeline remains portable and easy to reason about.

---

## Contributing

```bash
git checkout -b feature/<your-feature-name>
git add .
git commit -m "Describe your change"
git push origin feature/<your-feature-name>
```

Open a pull request for review once the change is ready.
