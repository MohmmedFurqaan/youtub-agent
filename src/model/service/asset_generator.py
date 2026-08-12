"""
Phase 2: Asset Generator
Generates all physical media assets (images, audio) from the structured JSON
video script produced by Phase 1, then assembles video-props.json for Remotion.

Faceless video format — no character images, single narrator voice.

Image generation: Pollinations.ai (free, no API key required)
TTS: edge-tts (Microsoft Neural Voices, free)
Duration: mutagen (accurate MP3 duration calculation)
"""

import asyncio
import json
import re
import time
import urllib.parse
from pathlib import Path

import edge_tts
import requests
from src.utility.logging_config import setup_logging
from src.utility.save_response import SaveLlmResponse
from mutagen.mp3 import MP3

# ── Constants ─────────────────────────────────────────────────────────────────
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
FPS = 30  # Remotion frame rate

# Single narrator voice for the faceless format
NARRATOR_VOICE = "en-US-ChristopherNeural"


class AssetGenerator:
    """
    Consumes the Phase 1 structured JSON script dict and produces:
      - data/metadata/scene/scene<n>_bg.png   (scene background)
      - data/metadata/scene/scene<n>.mp3      (TTS narration)
      - data/metadata/video-props.json        (Remotion props)

    Faceless format — no character portraits are generated.
    All paths stored in video-props.json are relative to video-renderer/public/
    so Remotion's staticFile() can serve them via the public/metadata symlink.
    """

    def __init__(self, script: dict):
        self.script = script
        self.logger = setup_logging()

        # Resolve project-root-relative paths
        project_root = Path(__file__).resolve().parents[3]
        self.scene_dir = project_root / "data" / "metadata" / "scene"

        # Ensure output directory exists
        self.scene_dir.mkdir(parents=True, exist_ok=True)

    # ── Public entry point ────────────────────────────────────────────────────

    def generate_assets(self) -> str:
        """
        Orchestrates all asset generation steps and writes video-props.json.

        Returns:
            Absolute path to the generated video-props.json as a string.
        """
        self.logger.info("=== Phase 2: Asset Generation Started ===")

        # Generate scene backgrounds + TTS audio and collect scene props
        scene_props = self._generate_scene_assets()

        # Assemble final Remotion props dict
        props = self._assemble_props(scene_props)

        # Persist to video-props.json
        saver = SaveLlmResponse(
            data=props,
            directory="data/metadata",
            filename="video-props.json",
        )
        saver.write_data()

        props_path = str(saver.json_file.resolve())
        self.logger.info("video-props.json written → %s", props_path)
        self.logger.info("=== Phase 2: Asset Generation Complete ===")
        return props_path

    # ── Scene assets ──────────────────────────────────────────────────────────

    def _generate_scene_assets(self) -> list[dict]:
        """
        For each scene: generate background image + TTS audio + calculate duration.

        Returns:
            List of scene prop dicts ready for Remotion.
        """
        scenes: list[dict] = self.script.get("scenes", [])
        scene_props: list[dict] = []

        for scene in scenes:
            n = scene.get("scene_number", len(scene_props) + 1)
            self.logger.info("Processing scene %d …", n)

            # ── Background image ──────────────────────────────────────────────
            bg_path = self._generate_background(scene, n)

            # ── TTS audio ─────────────────────────────────────────────────────
            audio_path, duration_frames = self._generate_tts(scene, n)

            scene_props.append(
                {
                    "scene_number": n,
                    "narration": scene.get("narration", ""),
                    "on_screen_text": scene.get("on_screen_text", ""),
                    "background_image": bg_path,
                    "audio_file": audio_path,
                    "duration_in_frames": duration_frames,
                }
            )

        return scene_props

    def _generate_background(self, scene: dict, scene_number: int) -> str:
        """Downloads and saves a background image for the scene.

        Returns:
            Remotion static path (e.g. "metadata/scene/scene1_bg.png")
            served via video-renderer/public/metadata symlink.
        """
        dest = self.scene_dir / f"scene{scene_number}_bg.png"
        static_path = f"metadata/scene/scene{scene_number}_bg.png"

        if dest.exists():
            self.logger.info("Background already exists, skipping: %s", dest)
            return static_path

        bg_prompt = scene.get(
            "background_prompt",
            "Abstract colorful digital background, cinematic, 9:16 aspect ratio",
        )
        self.logger.info("Generating background for scene %d …", scene_number)
        image_bytes = self._download_image(bg_prompt, width=576, height=1024)

        if image_bytes:
            dest.write_bytes(image_bytes)
            self.logger.info("Saved background → %s", dest)
            return static_path
        else:
            self.logger.warning("Failed to generate background for scene %d", scene_number)
            return ""

    def _generate_tts(self, scene: dict, scene_number: int) -> tuple[str, int]:
        """
        Generates an MP3 TTS file for the scene narration.

        Returns:
            (remotion_static_path, duration_in_frames)
            e.g. ("metadata/scene/scene1.mp3", 132)
        """
        dest = self.scene_dir / f"scene{scene_number}.mp3"
        static_path = f"metadata/scene/scene{scene_number}.mp3"

        if not dest.exists():
            narration: str = scene.get("narration", "")

            if narration.strip():
                self.logger.info(
                    "Generating TTS for scene %d (voice: %s) …", scene_number, NARRATOR_VOICE
                )
                try:
                    asyncio.run(self._async_tts(narration, NARRATOR_VOICE, str(dest)))
                    self.logger.info("Saved TTS audio → %s", dest)
                except Exception as exc:
                    self.logger.error(
                        "TTS failed for scene %d: %s", scene_number, exc
                    )
                    return "", 90  # fallback 3 s at 30 fps
            else:
                self.logger.warning("Scene %d has empty narration, skipping TTS.", scene_number)
                return "", 90

        # Calculate duration in frames from the physical file
        duration_frames = self._calculate_duration_frames(dest)
        return static_path, duration_frames

    @staticmethod
    async def _async_tts(text: str, voice: str, output_path: str) -> None:
        """Async helper that calls edge-tts to produce an MP3 file."""
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(output_path)

    @staticmethod
    def _calculate_duration_frames(mp3_path: Path) -> int:
        """Returns the audio length in Remotion frames (at FPS)."""
        try:
            audio = MP3(str(mp3_path))
            return max(1, round(audio.info.length * FPS))
        except Exception:
            return 90  # fallback 3 s

    # ── Pollinations.ai image download ────────────────────────────────────────

    def _download_image(
        self,
        prompt: str,
        width: int = 576,
        height: int = 1024,
        retries: int = 3,
    ) -> bytes | None:
        """
        Downloads an image from Pollinations.ai for the given prompt.
        Retries up to `retries` times on failure.
        """
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{POLLINATIONS_BASE}/{encoded_prompt}?width={width}&height={height}&nologo=true"

        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    return response.content
                self.logger.warning(
                    "Pollinations returned %d (attempt %d/%d)",
                    response.status_code, attempt, retries,
                )
            except requests.RequestException as exc:
                self.logger.warning(
                    "Request failed (attempt %d/%d): %s", attempt, retries, exc
                )
            time.sleep(2)  # brief pause before retry

        return None

    # ── Props assembly ────────────────────────────────────────────────────────

    def _assemble_props(self, scene_props: list[dict]) -> dict:
        """
        Builds the final video-props.json dict that Remotion will consume.
        Faceless format — no characters field.
        """
        return {
            "title": self.script.get("title", ""),
            "scenes": scene_props,
            "fps": FPS,
            "total_duration_frames": sum(
                s.get("duration_in_frames", 0) for s in scene_props
            ),
        }
