# Remotion Video Pipeline — Implementation Plan

## Overview

The `yt-agent` uses **Remotion** (React-based programmatic video renderer) to produce YouTube Shorts in a **faceless video format**. The pipeline is fully automated: the LLM generates a structured JSON script, Python downloads/generates all media assets, and Remotion renders the final MP4.

---

## Architecture

```
main.py
  │
  ├── Phase 1: VideoAgent (LLM)
  │     Gemini → structured JSON script
  │     → data/llm_response.json
  │
  ├── Phase 2: AssetGenerator (Python)
  │     Pollinations.ai → background images (per scene)
  │     edge-tts → MP3 narration (per scene)
  │     mutagen → frame duration calculation
  │     → data/metadata/video-props.json
  │     → data/metadata/scene/scene<n>_bg.png
  │     → data/metadata/scene/scene<n>.mp3
  │
  └── Phase 3: Remotion (Node.js)
        video-renderer/
          npm run render:props
        → video-renderer/out/video.mp4
```

---

## Video Format: Faceless

No host characters or portraits. A single invisible narrator delivers punchy commentary over full-screen cinematic backgrounds.

### Layout (1080×1920, 9:16 portrait)

```
┌─────────────────────────────┐
│                             │
│   [Ken Burns background]    │  ← Full-frame image, slow zoom + pan
│                             │
│  ╔═════════════════════╗    │
│  ║  ON SCREEN TEXT     ║    │  ← Keyword badge pill, gradient, top-center
│  ╚═════════════════════╝    │
│                             │
│   word  by  WORD  reveal    │  ← TikTok-style captions, groups of 4
│                             │
│  ███████████░░░░░░░░░░░░    │  ← Scene progress bar, very bottom
└─────────────────────────────┘
```

### Visual Features

| Feature | Implementation |
|---|---|
| **Ken Burns** | `interpolate()` scale 1.0→1.1 + alternating X/Y translate over `durationInFrames` |
| **Keyword badge** | Gradient pill (`#6C63FF → #FF6584`), fade+scale in on frames 0–10 |
| **Word captions** | Narration split into words, groups of 4, active word highlighted yellow (`#FFE066`) |
| **Progress bar** | Thin gradient bar at bottom, width = `frame / durationInFrames * 100%` |
| **Gradient overlay** | Top + bottom dark vignette for text legibility |

---

## File Structure

```
video-renderer/
├── package.json              ← scripts: start, render, render:props
├── tsconfig.json
├── public/
│   └── metadata → ../../data/metadata   ← symlink (assets served by Remotion)
└── src/
    ├── types.ts              ← VideoProps + Scene interfaces
    ├── index.tsx             ← registerRoot + Composition (1080×1920, 30fps)
    ├── MainComposition.tsx   ← <Series> over all scenes
    └── SceneRenderer.tsx     ← Ken Burns + badge + captions + progress bar
```

---

## JSON Schema (`video-props.json`)

```json
{
  "title": "Video Title",
  "fps": 30,
  "total_duration_frames": 996,
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Exact words the narrator speaks.",
      "on_screen_text": "KEYWORD BADGE",
      "background_image": "metadata/scene/scene1_bg.png",
      "audio_file": "metadata/scene/scene1.mp3",
      "duration_in_frames": 132
    }
  ]
}
```

> All paths are relative to `video-renderer/public/` and served via `staticFile()`.

---

## LLM Script Prompt (`prompts/script_video_prompt.md`)

The prompt forces the LLM to output **only valid JSON** matching the schema above.  
Key constraints:
- No `characters` or `speaker` fields (faceless format)
- 5–10 scenes, ~30–60 seconds total
- `narration`: max ~20 words per scene, punchy and direct
- `on_screen_text`: 2–5 words, bold impact phrase
- `background_prompt`: cinematic, 9:16, varies every 2 scenes

---

## Asset Generation (`model/service/asset_generator.py`)

| Step | Tool | Output |
|---|---|---|
| Background images | Pollinations.ai (`image.pollinations.ai/prompt/...`) | `scene<n>_bg.png` |
| TTS narration | `edge-tts` (`en-US-ChristopherNeural`) | `scene<n>.mp3` |
| Duration frames | `mutagen` (MP3 audio length × 30 fps) | `duration_in_frames` in props |

Assets are cached — if a file already exists on disk it won't be re-downloaded.

---

## npm Scripts

```bash
# Start Remotion Studio (live preview at localhost:3000)
npm run start

# Render to MP4 using current video-props.json
npm run render:props
# → out/video.mp4
```

---

## Known Issues & Resolutions

| Issue | Resolution |
|---|---|
| `TypeError: Cannot read properties of undefined (reading 'readFile')` | TypeScript 7.0 removed `sys` API. Pinned to `typescript@~5.8.3` in `dependencies`. |
| `Could not find composition with ID src/index.ts` | npm scripts referenced old `.ts` extension. Updated to `.tsx`. |
| 404 errors on absolute `/media/farkan/...` paths | Remotion static server only serves `public/`. Created `video-renderer/public/metadata` symlink → `../../data/metadata`. All props paths now use `metadata/...` prefix + `staticFile()`. |
