# YouTube Agent — Faceless Video Generator

An automated pipeline that turns any technical topic into a polished **YouTube Shorts-ready MP4** using Gemini AI, Pollinations.ai, Microsoft edge-tts, and Remotion.

## How it works

```
main.py
  │
  ├── Phase 1 — AI Script (Gemini via OpenRouter)
  │     Generates a structured JSON video script (scenes, narration, keywords)
  │     → data/llm_response.json
  │
  ├── Phase 2 — Asset Generation (Python)
  │     Background images  →  Pollinations.ai (free, no key needed)
  │     TTS narration      →  edge-tts (Microsoft Neural voices, free)
  │     → data/metadata/video-props.json
  │     → data/metadata/scene/scene<n>_bg.png
  │     → data/metadata/scene/scene<n>.mp3
  │
  └── Phase 3 — Video Render (Remotion / Node.js)
        Ken Burns backgrounds + word-by-word TikTok captions + progress bar
        → video-renderer/out/video.mp4
```

---

## Requirements

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | latest | see below |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| npm | 9+ | bundled with Node.js |

Install **uv** (Python package manager):
```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

## or to simple instala uv by pip
pip install uv

```

---


## Setup

### 1 — Clone the repo

```bash
git clone https://github.com/MohmmedFurqaan/youtub-agent.git
cd youtub-agent
git checkout feature/video-agent
```

### 2 — Install Python dependencies

```bash
uv sync
```

### 3 — Install Node.js dependencies (Remotion renderer)

```bash
cd video-renderer
npm install
cd ..
```

### 4 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

> You can also set `SYSTEM_VIDEO_PROMPT` in `.env` to override the default video script prompt.

---

## How to run

### Step 1 — Generate the script + assets (Python)

```bash
uv run main.py
```

This runs **Phase 1** (AI script generation) and **Phase 2** (image + audio asset download). Outputs:
- `data/llm_response.json` — raw LLM script
- `data/metadata/video-props.json` — Remotion props
- `data/metadata/scene/` — background PNGs + MP3s

> Assets are **cached** — re-running will skip already-generated files.

### Step 2 — Render the video (Node.js / Remotion)

```bash
cd video-renderer
npm run render:props
```

Output: `video-renderer/out/video.mp4`

> First render downloads Chrome Headless Shell (~27 MB, one-time only).

### (Optional) — Preview in Remotion Studio

```bash
cd video-renderer
npm run start
```

Opens a live preview at `http://localhost:3000`. Scrub through all scenes interactively.

---

## Project structure

```
yt-agent/
├── main.py                         ← Pipeline entry point (Phase 1 + 2)
├── prompts/
│   └── script_video_prompt.md      ← LLM system prompt (faceless format)
├── model/
│   ├── service/
│   │   ├── prompt_agent.py         ← Phase 1: Gemini script generation
│   │   └── asset_generator.py      ← Phase 2: image + TTS generation
│   └── utility/
│       ├── save_response.py        ← JSON persistence utility
│       └── logging_config.py       ← Logging setup
├── data/
│   ├── llm_response.json           ← Raw LLM output (generated)
│   └── metadata/
│       ├── video-props.json        ← Remotion props (generated)
│       └── scene/                  ← PNGs + MP3s per scene (generated)
├── video-renderer/                 ← Remotion project (Node.js)
│   ├── package.json
│   ├── public/
│   │   └── metadata → ../../data/metadata   ← symlink (static asset serving)
│   └── src/
│       ├── index.tsx               ← registerRoot + Composition
│       ├── MainComposition.tsx     ← Series of scenes
│       ├── SceneRenderer.tsx       ← Ken Burns + captions + progress bar
│       └── types.ts                ← VideoProps + Scene types
├── docs/                           ← Architecture docs
└── test/                           ← Test plans
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `uv: command not found` | Install uv — see Requirements above |
| `OPENROUTER_API_KEY not set` | Copy `.env.example` → `.env` and fill in the key |
| `Cannot read properties of undefined (reading 'readFile')` | TypeScript version issue — run `npm install typescript@~5.8.3` inside `video-renderer/` |
| 404 errors on image/audio in Remotion | Verify `video-renderer/public/metadata` symlink exists: `ls video-renderer/public/` |
| Chrome Headless Shell download fails | Check internet connection; Remotion downloads it once to a cache dir |

---

## Useful links

- [OpenRouter API key](docs/agent-api-key.md)
- [Remotion docs](https://www.remotion.dev/docs/)
- [uv docs](https://docs.astral.sh/uv/)
- [edge-tts voices](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Pollinations.ai](https://pollinations.ai/)
- [LangChain docs](https://docs.langchain.com/oss/python/langchain/quickstart)

---

## Contributing

```bash
git checkout -b feature/<your-feature-name>
git add .
git commit -m "describe your change"
git push origin feature/<your-feature-name>
```

Open a pull request or raise an issue on the [GitHub Issues](https://github.com/MohmmedFurqaan/youtub-agent/issues) page.
