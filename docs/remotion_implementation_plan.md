# video-generator, version : 0.1

This document outlines the professional implementation plan for integrating [Remotion](https://www.remotion.dev/) into the existing `yt-agent` to programmatically generate YouTube Shorts and standard videos. 

Currently, the `VideoAgent` generates a text prompt meant for AI video generators (like Luma, Pika, etc.). To use Remotion, we will transition the agent to generate a structured JSON script, create audio and image assets via Python, and then use Remotion to compile these assets into a polished MP4 using web technologies (React/CSS).

## Overview of the New Flow
1. **JSON Script Generation**: The LLM generates a structured JSON containing scenes, narrations, character dialogs (who is speaking), on-screen text, and background image prompts.
2. **Asset Generation (Python)**: Python processes the JSON to generate Text-to-Speech (TTS) audio and background images for each scene. It also maps custom user-uploaded character images (or generates default characters).
3. **Props Compilation**: Python bundles the paths to these assets (backgrounds, audio, character images) and their timings into a `props.json` file.
4. **Remotion Rendering**: Python spawns a subprocess to run the Remotion CLI. Remotion uses CSS to animate the static character images based on who is speaking (the "PNG-Tuber" approach).

---

## Step-by-Step Implementation Guide

### Phase 1: Update the AI Prompt for JSON Output
Remotion requires structured data to render scenes programmatically. The current text-based prompt must be converted to output strict JSON.

**Changes Required:**
1. Modify `prompts/script_video_prompt.md` to instruct the LLM to output ONLY valid JSON.
2. The AI must script a conversation between characters (e.g., "Host" and "Guest").
3. Use the following JSON schema as the target output structure:
```json
{
  "title": "Understanding APIs",
  "characters": ["Host", "Guest"],
  "scenes": [
    {
      "scene_number": 1,
      "speaker": "Host",
      "narration": "This one concept changed software forever.",
      "on_screen_text": "APIs EXPLAINED",
      "background_prompt": "A modern, glowing digital connection between two servers, cinematic lighting, 9:16 aspect ratio"
    },
    ...
  ]
}
```
4. In `model/service/prompt_agent.py`, update `video_script_generator` to parse the returned JSON string into a Python dictionary (`json.loads()`).

### Phase 2: Python Asset Generation (TTS & Images)
Before Remotion can render, it needs the actual media files. 

**Changes Required:**
1. Create a new module (e.g., `model/service/asset_generator.py`).
2. **Character Upload Management**: 
   - Allow the user to upload custom `.png` files with transparent backgrounds for each character (e.g., `Host.png`, `Guest.png`).
   - If a custom image isn't provided, use an AI Image API (like Pollinations.ai or DALL-E) to generate a character on a solid background, then use the **`rembg`** Python library (recommended: `uv add rembg` or fallback to `pip install rembg`) to automatically strip the background.
   - Save these transparent images to `data/metadata/characters/`.
3. **Text-to-Speech (TTS) using edge-tts**: Loop through `scenes` and use the `edge-tts` Python library to generate the audio for the `narration`. Assign different built-in Microsoft Edge voices based on the `speaker` (e.g., "en-US-ChristopherNeural" for Host, "en-US-AriaNeural" for Guest). Save the output as `.mp3` files in `data/metadata/scene/`. This provides high-quality, completely free TTS without needing API keys.
4. **Background Generation**: Generate background images based on `background_prompt`. Save them as `.png`/`.jpg` in `data/metadata/scene/`.
5. **Duration Calculation**: Use a library like `mutagen` or `pydub` in Python to calculate the exact duration (in seconds/frames) of each audio file so Remotion knows how long each scene should be.
6. Save a final `video-props.json` in `data/metadata/` that maps these assets. **CRITICAL: Use the existing `SaveLlmResponse` utility from `model/utility/save_response.py` to handle all JSON file reading and writing:**
```json
{
  "fps": 30,
  "characters": {
    "Host": "/absolute/path/to/data/metadata/characters/Host.png",
    "Guest": "/absolute/path/to/data/metadata/characters/Guest.png"
  },
  "scenes": [
    {
      "durationInFrames": 120,
      "speaker": "Host",
      "audioPath": "/absolute/path/to/data/metadata/scene/scene1.mp3",
      "backgroundPath": "/absolute/path/to/data/metadata/scene/scene1.png",
      "onScreenText": "APIs EXPLAINED"
    }
  ]
}
```

### Phase 3: Setup the Remotion Project
Remotion runs in a Node.js environment. We will create a standalone Remotion app within the project repository.

**Changes Required:**
1. Run `npx create-video@latest video-renderer` in the root of `yt-agent`.
2. Inside `video-renderer/src`, create a `MainComposition.tsx` that accepts the JSON structure defined above as its React Props.
3. The composition will use Remotion's `<Series>` and `<Sequence>` components to iterate through the scenes:
    - Display the `<Img src={staticFile(scene.backgroundPath)} />` as the base background.
    - Overlay the Character Images side-by-side or alternating.
    - **Animation Trick**: Read the `scene.speaker` property. If "Host" is speaking, apply a CSS animation (e.g., a slight scale/bounce using `spring()` or `interpolate()`) to `Host.png` while slightly dimming `Guest.png`, and vice-versa.
    - Play the `<Audio src={staticFile(scene.audioPath)} />`.
    - Animate the `scene.onScreenText` using React/CSS.

### Phase 4: Orchestrate the Render from Python
Finally, the Python agent needs to trigger the Remotion CLI to render the video automatically.

**Changes Required:**
1. Create a new module `model/service/video_renderer.py`.
2. Use Python's `subprocess` module to call the Remotion CLI.
3. Pass the absolute path of the generated `props.json` via the CLI arguments.

**Example Python Code:**
```python
import subprocess
import os

class RemotionRenderer:
    def __init__(self, remotion_dir="video-renderer"):
        self.remotion_dir = remotion_dir

    def render(self, props_path, output_mp4_path):
        # npx remotion render src/index.ts MainComposition out.mp4 --props ./video-props.json
        command = [
            "npx", "remotion", "render", 
            "src/index.ts", "MainComposition", 
            output_mp4_path,
            f"--props={props_path}"
        ]
        
        try:
            subprocess.run(command, cwd=self.remotion_dir, check=True)
            print(f"Video successfully rendered at {output_mp4_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to render video: {e}")
```

### Phase 5: Bring it all together in `main.py`
Update `main.py` to chain these services sequentially:
1. `video_script = ai_prompt_agent.video_script_generator()` (Returns JSON)
2. `props_file = asset_generator.generate_assets(video_script)` (Generates Audio/Images, returns path to `video-props.json`)
3. `renderer.render(props_file, "data/metadata/video/final_video.mp4")` (Triggers Remotion and saves the `.mp4` into the `data/metadata/video/` directory)
4. Finally, update `data/metadata/youtube-data.json` with the path to the generated MP4 file, utilizing the `SaveLlmResponse` utility class for file handling.

---

## Summary of File Modifications
- **Modified**: `prompts/script_video_prompt.md` (Update to strictly output JSON schema).
- **Modified**: `model/service/prompt_agent.py` (Parse JSON output instead of handling plain text).
- **Modified**: `main.py` (Orchestrate the new pipeline: LLM -> Asset Generation -> Remotion).
- **New**: `model/service/asset_generator.py` (Handle TTS and Image API calls).
- **New**: `model/service/video_renderer.py` (Handle subprocess execution for Remotion).
- **New Folder**: `video-renderer/` (Contains the standalone React Remotion project).
