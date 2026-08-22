# YouTube Agent Studio

An autonomous YouTube Shorts generator and publishing suite powered by **OpenRouter LLMs**, **Grok Imagine AI Video (KIE.ai)**, **Edge-TTS**, **FFmpeg Compositor**, **FastAPI**, and a **2D Flat React + shadcn/ui Web Application**.

---

## 🚀 Features

- **Full-Stack Web Interface**: Modern, responsive 2D flat Studio UI built with React, Vite, Tailwind CSS v4, and **shadcn/ui** components.
- **Real-Time Progress Monitor**: Live Server-Sent Events (SSE) log stream tracking 5 pipeline stages:
  1. *Script & VideoPlan Generation*
  2. *Grok Imagine 30s Vertical AI Video Generation*
  3. *Edge-TTS Narration & SRT Subtitle Synthesis*
  4. *FFmpeg Audio/Video Composition & Subtitle Burning*
  5. *Automated Quality Gate Checks*
- **Media Library & Inspector**: Preview `final.mp4` with embedded HTML5 player, listen to narration audio, view subtitles, edit `plan.json` directly, and inspect quality metrics.
- **YouTube Publishing Suite**: Validate quality gate compliance and publish videos directly to YouTube (Public or Private mode).
- **CLI & REST API Support**: Full feature parity between Web UI and terminal CLI (`main.py`).

---

## 📐 Architecture

```
Topic Prompt
  → OpenRouter LLM (Gemini / Nemotron)   — generates VideoPlan JSON
  → Grok Imagine AI Video (KIE.ai)        — generates 30s 9:16 vertical video
  → Edge-TTS                             — synthesizes narration audio + SRT subtitles
  → FFmpeg Compositor                    — merges video, audio & burns subtitles
  → Quality Gate Checks                   — validates audio/video sync & resolution
  → YouTube Data API                      — uploads video (Private by default)
```

---

## ⚙️ Quick Start & Setup

### 1. Install Python Dependencies

```bash
uv sync
```

### 2. Install Frontend Dependencies & Build Web UI

```bash
cd web
npm install
npm run build
cd ..
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `OPENROUTER_MODEL_NAME` | e.g. `google/gemini-2.5-flash` |
| `KIE_API_KEY` | KIE.ai API key for Grok Imagine Text-to-Video |
| `YOUTUBE_CLIENT_ID` | YouTube OAuth Client ID |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth Client Secret |
| `YOUTUBE_PROJECT_ID` | Google Cloud Project ID |

---

## 🖥️ Running the Web Application

Launch the FastAPI backend and serve the Web UI:

```bash
uv run python main.py web --port 8000
```

Open your browser at **`http://localhost:8000`**!

### Frontend Development Mode (Hot Reloading)

To work on the React UI with hot reload:

```bash
# Terminal 1 (Backend API)
uv run python main.py web --port 8000

# Terminal 2 (Vite Dev Server)
cd web && npm run dev
```

Open `http://localhost:5173`.

---

## 💻 CLI Usage

You can also run pipeline actions directly from the command line:

### Generate a new video from topic

```bash
uv run python main.py create --topic "How an API request works under the hood"
```

### Use a cached plan (skips LLM call)

```bash
uv run python main.py create --topic "..." --use-cached-plan data/runs/<run_id>/plan.json
```

### Upload a run to YouTube

```bash
# Private Upload (default)
uv run python main.py upload --run-id <run_id>

# Public Upload
uv run python main.py upload --run-id <run_id> --publish
```

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
uv run pytest
```

---

## 📁 Run Directory Structure

Each execution creates an isolated run directory in `data/runs/<run_id>`:

```
data/runs/<run-id>/
  ├── plan.json          — Video script & motion prompts
  ├── raw/
  │   └── final.mp4      — Raw 30s AI video from Grok Imagine
  ├── audio/
  │   ├── narration.mp3  — TTS voiceover audio
  │   └── captions.srt   — SRT subtitle captions
  ├── final.mp4          — Rendered final output (video + audio + burned captions)
  └── run.json           — Execution status, timestamps, and log paths
```
