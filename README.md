# yt-agent

Automated YouTube Shorts generator powered by NVIDIA Nemotron and Remotion.

> **This project does not use text-to-video generation.**
> Remotion composes licensed/static visual assets, programmatic diagrams,
> narration, captions, and overlays into the final MP4.

---

## Architecture

```
Topic
  → NVIDIA Nemotron (OpenRouter)  — generates VideoPlan JSON
  → Asset Resolver                — diagrams (SVG) or still images
  → TTS (edge-tts)               — one narration.mp3 + captions.json
  → Remotion                     — renders 1080×1920 @30fps MP4
  → Quality checks (ffprobe)     — validates before upload is allowed
  → YouTube upload               — explicit separate command, private by default
```

---

## Setup

### 1. Install Python dependencies

```bash
uv sync
```

### 2. Install Node dependencies (Remotion renderer)

```bash
cd video-renderer && npm install && cd ..
```

### 3. Configure environment

Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

Required variables:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `OPENROUTER_MODEL_NAME` | e.g. `nvidia/nemotron-3.5-lightning:free` |
| `YOUTUBE_CLIENT_ID` | YouTube OAuth client ID |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth client secret |
| `YOUTUBE_PROJECT_ID` | Google Cloud project ID |

Optional:

| Variable | Default | Description |
|---|---|---|
| `USE_POLLINATIONS_STILL` | `false` | Enable Pollinations.ai still-image backgrounds |

### 4. FFmpeg

The quality checker requires `ffprobe` (included with FFmpeg):

```bash
# Ubuntu / Debian
sudo apt install ffmpeg
```

---

## Usage

### Generate a video

```bash
uv run python main.py create --topic "How an API request works"
```

This runs the full pipeline and prints a **Run ID** when complete.

### Re-use a cached plan (skip LLM call)

```bash
uv run python main.py create --topic "..." --use-cached-plan data/runs/<id>/plan.json
```

### Upload to YouTube (private by default)

```bash
uv run python main.py upload --run-id <id>
```

### Upload and make public

```bash
uv run python main.py upload --run-id <id> --publish
```

Upload is always a **separate, explicit command** so a render failure cannot
accidentally make a video public.

---

## Preview in Remotion Studio

```bash
cd video-renderer && npm run dev
```

---

## Run tests

```bash
uv run python -m pytest test/ -v
```

---

## Run directory layout

Each video generation produces an immutable run directory:

```
data/runs/<run-id>/
  plan.json          — validated VideoPlan (NVIDIA output)
  props.json         — Remotion composition input
  assets/
    scene-01/
      asset.svg      — diagram or image
      asset.json     — manifest (source, license, attribution)
    scene-02/ …
  audio/
    narration.mp3    — single TTS narration for the full video
  captions.json      — Remotion-compatible word timestamps
  final.mp4          — rendered output
  run.json           — pipeline status, paths, errors
  youtube.json       — video ID and upload timestamp (after upload)
```

---

## Visual asset strategy

| Scene `visual.kind` | Resolver | External API? |
|---|---|---|
| `diagram` | `DiagramResolver` (SVG text+icon) | ❌ None |
| `image` | `StillImageResolver` (Pollinations) | ⚙️ Only if `USE_POLLINATIONS_STILL=true` |
| `stock_video` | `LocalAssetResolver` (`data/library/`) | ❌ None |
| `screen_capture` | `LocalAssetResolver` (`data/library/`) | ❌ None |

---

## Removed

The following text-to-video API integrations have been removed:

- Seedance 2.5 (`KIE_API_KEY`)
- Veo 3.1
- Grok / api.kie.ai

The `KIE_API_KEY` environment variable is no longer used or loaded.
