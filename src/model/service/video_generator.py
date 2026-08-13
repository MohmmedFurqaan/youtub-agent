"""
Seedance 2.5 Video Generator

Orchestrates the end-to-end video generation workflow:
    1. Build a comprehensive prompt from the video script
    2. Submit a single 30-second generation task via SeedanceClient
    3. Poll until the task completes
    4. Download the resulting MP4

This replaces the old Veo-based VideoGeneratorAgent with a cleaner,
single-responsibility design that matches the Seedance 2.5 API contract.
"""

import json
import time
from pathlib import Path

import requests

from src.model.client.seedance_client import SeedanceClient
from src.utility.logging_config import setup_logging


class SeedanceVideoGenerator:
    """Generates a single 30-second video from a structured video script.

    The generator consolidates the visual_bible and all scene descriptions
    into one rich prompt, submits it to the Seedance 2.5 API, and downloads
    the result.

    Attributes:
        POLL_INTERVAL:  Seconds between status checks (default 30).
        POLL_MAX:       Maximum polling attempts before timeout (default 40 → 20 min).
    """

    POLL_INTERVAL = 30
    POLL_MAX = 40

    def __init__(
        self,
        script: dict,
        api_key: str,
        script_id: str,
        reference_image_urls: list[str] | None = None,
    ):
        """Initialize the video generator.

        Args:
            script:               Structured video script dict from the LLM.
            api_key:              KIE API key for Seedance authentication.
            script_id:            UUID from llm_response.json for folder naming.
            reference_image_urls: Optional reference images for style/character guidance.
        """
        self._script = script
        self._script_id = script_id
        self._reference_image_urls = reference_image_urls or []
        self._client = SeedanceClient(api_key)
        self._logger = setup_logging(__name__)

        # Output directory: data/{script_id}/
        self._project_root = Path(__file__).resolve().parents[3]
        self._output_dir = self._project_root / "data" / self._script_id
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ───────────────────────────────────────────────────────────

    def generate_video(self) -> dict:
        """Run the full generation pipeline.

        Returns:
            Dict with keys:
                - video_path: Absolute path to the downloaded MP4 (or None).
                - task_id:    The Seedance task ID.
                - state:      Final task state ("success" or "fail").
                - error:      Error message if generation failed (or None).
        """
        # 1. Build prompt
        prompt = self._build_prompt()
        self._logger.info("[generator] Prompt built (%d chars)", len(prompt))

        # 2. Extract video params from script
        video_config = self._script.get("video", {})
        aspect_ratio = video_config.get("aspect_ratio", "9:16")
        resolution = video_config.get("resolution", "720p")
        duration = video_config.get("target_duration", 30)

        # Merge reference images from script + constructor
        script_refs = self._script.get("reference_image_urls", [])
        all_refs = list(set(self._reference_image_urls + script_refs))

        # 3. Submit task
        try:
            task_id = self._client.create_task(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                reference_image_urls=all_refs if all_refs else None,
            )
        except RuntimeError as e:
            self._logger.error("[generator] Task creation failed: %s", e)
            return {"video_path": None, "task_id": None, "state": "fail", "error": str(e)}

        # 4. Poll until complete
        result = self._poll_until_complete(task_id)
        state = result.get("data", {}).get("state", "").lower()

        if state != "success":
            fail_msg = result.get("data", {}).get("failMsg", "Unknown error")
            self._logger.error("[generator] Task %s failed: %s", task_id, fail_msg)
            return {"video_path": None, "task_id": task_id, "state": state, "error": fail_msg}

        # 5. Extract result URL and download
        video_url = self._extract_result_url(result)
        if not video_url:
            return {
                "video_path": None,
                "task_id": task_id,
                "state": "success",
                "error": "No result URL in response",
            }

        video_path = self._download_video(video_url)
        return {
            "video_path": str(video_path) if video_path else None,
            "task_id": task_id,
            "state": "success",
            "error": None,
        }


    def _build_prompt(self) -> str:
        """Consolidate the full script into a single Seedance prompt.

        Combines the visual_bible directives with all scene descriptions
        to produce one coherent generation prompt.
        """
        visual_bible = self._script.get("visual_bible", {})
        scenes = self._script.get("scenes", [])

        parts = []

        # Visual identity
        parts.append("VISUAL DIRECTION")
        parts.append(f"Style: {visual_bible.get('visual_style', 'natural realistic')}")
        parts.append(f"Environment: {visual_bible.get('environment', '')}")
        parts.append(f"Lighting: {visual_bible.get('lighting', '')}")

        palette = visual_bible.get("color_palette", [])
        if palette:
            parts.append(f"Color Palette: {', '.join(palette)}")

        parts.append(f"Camera: {visual_bible.get('camera_style', '')}")

        objects = visual_bible.get("objects", [])
        if objects:
            parts.append(f"Key Objects: {', '.join(objects)}")

        rules = visual_bible.get("continuity_rules", [])
        if rules:
            parts.append("Continuity Rules:")
            for rule in rules:
                parts.append(f"- {rule}")

        # Reference images
        refs = self._script.get("reference_image_urls", []) + self._reference_image_urls
        if refs:
            parts.append("")
            parts.append("REFERENCE IMAGES")
            for i, url in enumerate(refs, 1):
                parts.append(f"@Image{i}: {url}")

        # Scene descriptions
        parts.append("")
        parts.append("VIDEO SEQUENCE (30 seconds total)")

        for scene in scenes:
            scene_num = scene.get("scene_number", "?")
            duration = scene.get("duration", 7)
            parts.append("")
            parts.append(f"SCENE {scene_num} ({duration}s):")
            parts.append(f"Purpose: {scene.get('purpose', '')}")
            parts.append(f"Visual: {scene.get('background_prompt', '')}")

        return "\n".join(parts)


    def _poll_until_complete(self, task_id: str) -> dict:
        """Poll the Seedance API until the task reaches a terminal state.

        Terminal states: "success", "fail".

        Args:
            task_id: The task ID to poll.

        Returns:
            The final API response dict.
        """
        self._logger.info("[poll] Waiting for task %s ...", task_id)

        for attempt in range(1, self.POLL_MAX + 1):
            time.sleep(self.POLL_INTERVAL)

            resp = self._client.query_task(task_id)
            data = resp.get("data", {})
            state = str(data.get("state", "")).lower()

            self._logger.info(
                "[poll] Attempt %d/%d — taskId=%s state=%s",
                attempt, self.POLL_MAX, task_id, state,
            )

            if state == "success":
                self._logger.info("[poll] Task %s completed successfully.", task_id)
                return resp

            if state == "fail":
                fail_msg = data.get("failMsg", "unknown")
                self._logger.error("[poll] Task %s failed: %s", task_id, fail_msg)
                return resp

        self._logger.error("[poll] Task %s timed out after %d attempts.", task_id, self.POLL_MAX)
        return {"code": 408, "msg": "Polling timed out", "data": {"taskId": task_id, "state": "timeout"}}


    @staticmethod
    def _extract_result_url(resp: dict) -> str | None:
        """Parse the resultJson field to extract the first video URL.

        The Seedance API returns resultJson as a JSON string:
            '{"resultUrls": ["https://..."]}'
        """
        result_json_str = resp.get("data", {}).get("resultJson", "")
        if not result_json_str:
            return None

        try:
            result_data = json.loads(result_json_str)
            urls = result_data.get("resultUrls", [])
            return urls[0] if urls else None
        except (json.JSONDecodeError, TypeError, IndexError):
            return None

    # ── Download ─────────────────────────────────────────────────────────────

    def _download_video(self, url: str) -> Path | None:
        """Download the generated video to the output directory.

        Args:
            url: Direct URL to the MP4 file.

        Returns:
            Path to the saved file, or None on failure.
        """
        output_path = self._output_dir / "video.mp4"

        self._logger.info("[download] Downloading video → %s", output_path)
        self._logger.info("[download] URL: %s", url)

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            size = output_path.stat().st_size
            self._logger.info("[download] Saved: %s (%s bytes)", output_path, f"{size:,}")
            return output_path

        except requests.RequestException as e:
            self._logger.error("[download] Failed: %s", e)
            return None