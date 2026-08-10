# Remotion Integration Test Plan

This document outlines the testing strategy for the integration of Remotion into the `yt-agent` video generation pipeline. The integration is divided into 5 phases. As each phase is completed, its detailed test cases and status will be documented here.

## Phase 1: AI Prompt and JSON Output (COMPLETED)

**Objective**: Ensure the LLM generates a strictly formatted JSON video script and the `VideoAgent` parses it correctly into a Python dictionary.

### Test Cases

| Test ID | Component | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P1.1** | Prompt File | Verify strict JSON instructions in prompt file. | 1. Open `prompts/script_video_prompt.md`.<br>2. Check for the JSON schema and rules preventing markdown. | File contains exact JSON schema for `title`, `characters`, and `scenes`. | ✅ Passed |
| **P1.2** | JSON Parsing | Verify successful parsing of raw JSON. | 1. Mock the LLM response to return a raw valid JSON string.<br>2. Call `video_script_generator()`. | Returns a Python `dict` with the parsed JSON data. | ⬜ Pending |
| **P1.3** | Markdown Stripping | Verify stripping of ` ```json ` blocks. | 1. Mock the LLM response to return JSON wrapped in ` ```json ... ``` `.<br>2. Call `video_script_generator()`. | Returns a Python `dict`. Strips backticks successfully. | ⬜ Pending |
| **P1.4** | Markdown Stripping | Verify stripping of generic ` ``` ` blocks. | 1. Mock the LLM response to return JSON wrapped in ` ``` ... ``` `.<br>2. Call `video_script_generator()`. | Returns a Python `dict`. Strips backticks successfully. | ⬜ Pending |
| **P1.5** | Invalid JSON Handling | Verify graceful failure on invalid JSON. | 1. Mock the LLM response to return invalid JSON.<br>2. Call `video_script_generator()`. | Returns dict: `{"error": "Failed to parse JSON", "raw_content": ...}`. | ⬜ Pending |
| **P1.6** | Title Generation Types | Verify `ai_title_prompt` accepts dict inputs. | 1. Pass a valid `dict` to `ai_title_prompt()`. | `json.dumps()` is called and title is generated successfully. | ⬜ Pending |
| **P1.7** | E2E Generation | Verify live LLM call returns expected schema. | 1. Run `main.py`.<br>2. Observe terminal output. | Prints valid Python dict with `title`, `characters`, and `scenes`. | ✅ Passed |

---

## Phase 2: Python Asset Generation (TTS & Images) ✅ COMPLETED

**Objective**: Verify that `AssetGenerator` correctly consumes the Phase 1 JSON script dict and produces all physical media assets, then assembles a valid `video-props.json` for downstream Remotion consumption.

**Components Under Test**:
- `model/service/asset_generator.py` → `AssetGenerator` class
- `model/utility/save_response.py` → `SaveLlmResponse` (directory auto-creation)
- Pollinations.ai image API (character portraits + scene backgrounds)
- `edge-tts` (Microsoft Neural TTS)
- `mutagen` (MP3 duration calculation)

---

### 2.1 — Directory & File Creation

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.1.1** | `characters/` directory created automatically | 1. Delete `data/metadata/characters/`.<br>2. Run `main.py`. | Directory `data/metadata/characters/` exists after run. | ✅ Passed |
| **P2.1.2** | `scene/` directory created automatically | 1. Delete `data/metadata/scene/`.<br>2. Run `main.py`. | Directory `data/metadata/scene/` exists after run. | ✅ Passed |
| **P2.1.3** | `SaveLlmResponse` creates nested directories | 1. Pass `directory="data/metadata"`, `filename="video-props.json"` to `SaveLlmResponse`.<br>2. Call `write_data()`. | All parent directories are created; no `FileNotFoundError`. | ✅ Passed |
| **P2.1.4** | `video-props.json` file created at correct path | 1. Run `main.py`.<br>2. Check path logged in terminal. | File exists at `data/metadata/video-props.json`. | ✅ Passed |

---

### 2.2 — Character Image Generation (Pollinations.ai)

> **Reference Run**: 2 characters — `Host`, `Guest`. Both images generated and saved.

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.2.1** | Portrait generated for each character in script | 1. Run pipeline with `characters: ["Host", "Guest"]`.<br>2. Check `data/metadata/characters/`. | `Host.png` and `Guest.png` exist and are non-zero bytes. | ✅ Passed |
| **P2.2.2** | Existing character image is NOT re-downloaded | 1. Run `main.py` twice in a row.<br>2. Check logs on second run. | Log shows `"Character image already exists, skipping"` — no new download. | ✅ Passed |
| **P2.2.3** | Character image path stored in `video-props.json` | 1. Open `data/metadata/video-props.json`.<br>2. Inspect `characters` key. | Dict maps `"Host"` → absolute path string ending in `characters/Host.png`. | ✅ Passed |
| **P2.2.4** | Image dimensions are portrait (9:16) | 1. Open any `characters/*.png` in an image viewer. | Image is portrait-oriented (576 × 1024 px). | ⬜ Pending |
| **P2.2.5** | Pollinations retry on transient failure | 1. Mock `requests.get` to fail twice, then succeed on 3rd attempt.<br>2. Instantiate `AssetGenerator` and call `generate_assets()`. | Image is saved; log shows 2 warnings and 1 success. | ⬜ Pending |

---

### 2.3 — Scene Background Generation (Pollinations.ai)

> **Reference Run**: 6 scenes → `scene1_bg.png` … `scene6_bg.png` all saved successfully.

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.3.1** | Background image generated for every scene | 1. Run pipeline.<br>2. Count files in `data/metadata/scene/` matching `*_bg.png`. | Exactly 6 background images exist (`scene1_bg.png` → `scene6_bg.png`). | ✅ Passed |
| **P2.3.2** | Background image uses scene's `background_prompt` | 1. Inspect `background_prompt` field of scene 1 in Phase 1 output.<br>2. Confirm the downloaded image is semantically consistent. | Image appears to reflect the prompt (cinematic holographic nodes). | 🔍 Manual |
| **P2.3.3** | Existing background skipped on re-run | 1. Run `main.py` twice.<br>2. Inspect logs on 2nd run. | Log shows `"Background already exists, skipping"` for all scenes. | ✅ Passed |
| **P2.3.4** | Fallback prompt used when `background_prompt` is missing | 1. Pass a scene dict with no `background_prompt` key.<br>2. Call `_generate_background()`. | Uses default `"Abstract colorful digital background…"` fallback. | ⬜ Pending |

---

### 2.4 — Text-to-Speech Audio Generation (edge-tts)

> **Reference Run**: 6 `.mp3` files generated. Voice assignments: Host → `en-US-ChristopherNeural`, Guest → `en-US-AriaNeural`.

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.4.1** | MP3 generated for every scene | 1. Run pipeline.<br>2. Count files matching `scene*.mp3` in `data/metadata/scene/`. | Exactly 6 MP3 files exist (`scene1.mp3` → `scene6.mp3`). | ✅ Passed |
| **P2.4.2** | Host scenes use Christopher voice | 1. Inspect log lines for scene 1, 2, 4, 6 (speaker: Host).<br>2. Check voice logged. | Log shows `voice: en-US-ChristopherNeural` for Host scenes. | ✅ Passed |
| **P2.4.3** | Guest scenes use Aria voice | 1. Inspect log lines for scene 3, 5 (speaker: Guest).<br>2. Check voice logged. | Log shows `voice: en-US-AriaNeural` for Guest scenes. | ✅ Passed |
| **P2.4.4** | Unknown speaker falls back to default voice | 1. Pass a scene with `"speaker": "Narrator"` (not in `VOICE_MAP`).<br>2. Run `_generate_tts()`. | Uses `en-US-GuyNeural` (the `_default` voice). | ⬜ Pending |
| **P2.4.5** | Empty narration skips TTS generation | 1. Pass a scene with `"narration": ""`.<br>2. Call `_generate_tts()`. | Returns `("", 90)` — no MP3 file created, no error raised. | ⬜ Pending |
| **P2.4.6** | Existing MP3 is NOT re-generated | 1. Run `main.py` twice.<br>2. Note file modification times on 2nd run. | `scene*.mp3` timestamps remain unchanged on the 2nd run. | ✅ Passed |
| **P2.4.7** | Audio is audible and matches narration text | 1. Play `data/metadata/scene/scene1.mp3`.<br>2. Listen to content. | Audio says *"What if you could talk to any app without writing a single line of code?"* | 🔍 Manual |

---

### 2.5 — Duration Calculation (mutagen)

> **Reference Run durations** (at 30 fps):
> Scene 1: 132 fr (~4.4 s) · Scene 2: 196 fr (~6.5 s) · Scene 3: 161 fr (~5.4 s)
> Scene 4: 215 fr (~7.2 s) · Scene 5: 167 fr (~5.6 s) · Scene 6: 125 fr (~4.2 s)

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.5.1** | `duration_in_frames` is a positive integer | 1. Open `video-props.json`.<br>2. Check `duration_in_frames` for all 6 scenes. | All values are positive integers (`> 0`). | ✅ Passed |
| **P2.5.2** | Frame count matches audio length × 30 | 1. Use `mutagen` to read `scene1.mp3` duration manually.<br>2. Compute `round(length * 30)`.<br>3. Compare to `video-props.json` scene 1 value. | Manual calculation equals `132` frames. | ✅ Passed |
| **P2.5.3** | `total_duration_frames` is sum of all scene durations | 1. Sum all `duration_in_frames` values from `video-props.json`.<br>2. Compare to `total_duration_frames` field. | `132 + 196 + 161 + 215 + 167 + 125 = 996` matches `"total_duration_frames": 996`. | ✅ Passed |
| **P2.5.4** | Fallback duration used on corrupt MP3 | 1. Mock `MP3()` to raise an exception.<br>2. Call `_calculate_duration_frames()`. | Returns `90` (fallback = 3 s at 30 fps). | ⬜ Pending |

---

### 2.6 — `video-props.json` Schema Validation

> **Reference File**: `data/metadata/video-props.json` (generated 2026-08-10)

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.6.1** | Top-level keys are correct | 1. Open `video-props.json`.<br>2. Check keys present. | Contains exactly: `title`, `characters`, `scenes`, `fps`, `total_duration_frames`. | ✅ Passed |
| **P2.6.2** | `title` matches Phase 1 JSON | 1. Compare `title` in `video-props.json` to Phase 1 output. | `"MCP Servers Explained"` — exact match. | ✅ Passed |
| **P2.6.3** | `characters` maps names to absolute paths | 1. Check `characters` object in `video-props.json`. | `{"Host": "/…/Host.png", "Guest": "/…/Guest.png"}` — absolute paths. | ✅ Passed |
| **P2.6.4** | Each scene has all required fields | 1. Iterate all 6 scenes in `video-props.json`.<br>2. Check each for required keys. | Each scene has: `scene_number`, `speaker`, `narration`, `on_screen_text`, `background_image`, `audio_file`, `duration_in_frames`. | ✅ Passed |
| **P2.6.5** | All file paths in JSON are absolute and exist on disk | 1. For each `background_image` and `audio_file` path in `video-props.json`.<br>2. Run `os.path.exists()` on each. | All 12 paths (6 backgrounds + 6 audio files) resolve to existing files. | ✅ Passed |
| **P2.6.6** | `fps` is `30` | 1. Check `fps` field. | Value is integer `30`. | ✅ Passed |

---

### 2.7 — End-to-End Integration

| Test ID | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **P2.7.1** | Full pipeline runs without errors | 1. Run `uv run main.py`.<br>2. Observe exit code and terminal output. | Exit code `0`. Terminal prints `✔ All assets generated successfully.` | ✅ Passed |
| **P2.7.2** | Pipeline is idempotent (safe to re-run) | 1. Run `main.py` twice in a row.<br>2. Compare `video-props.json` on both runs. | 2nd run skips existing files. Output `video-props.json` is identical. | ✅ Passed |
| **P2.7.3** | `main.py` chains Phase 1 → Phase 2 correctly | 1. Verify `main.py` passes Phase 1 dict directly into `AssetGenerator(script=video_script)`. | `AssetGenerator` receives the full structured dict; no serialization step needed. | ✅ Passed |

---

## Phase 3: Setup the Remotion Project (PENDING)

*Test cases will be defined once this phase is shipped.*

---

## Phase 4: Orchestrate the Render from Python (PENDING)

*Test cases will be defined once this phase is shipped.*

---

## Phase 5: Bring it all together in `main.py` (PENDING)

*Test cases will be defined once this phase is shipped.*
