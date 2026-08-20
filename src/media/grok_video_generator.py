"""
src/media/grok_video_generator.py

Client for KIE.ai Grok Imagine Text-To-Video API (grok-imagine/text-to-video).
Generates a 30-second AI video directly from a text motion prompt.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
import requests

from src.utility.file_manipulator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()


class GrokVideoGenerator:
    """Client for generating AI videos via Grok Imagine API."""

    CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
    RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
    MODEL_NAME = "grok-imagine/text-to-video"

    def __init__(self, kie_api_key: str) -> None:
        if not kie_api_key:
            raise ValueError("KIE_API_KEY must be provided.")
        self.api_key = kie_api_key.strip()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_video(
        self,
        prompt: str,
        run_dir: Path,
        aspect_ratio: str = "9:16",
        duration: int = 30,
        resolution: str = "480p",
        mode: str = "normal",
        nsfw_checker: bool = True,
        poll_interval: int | None = None,
        timeout: int | None = None,
    ) -> Path:
        """Create task, poll until completed, download MP4, and save to run_dir/final.mp4.

        Args:
            prompt: Text prompt describing the desired video motion (will be stripped).
            run_dir: Run folder path where final.mp4 will be saved.
            aspect_ratio: Video aspect ratio ("9:16" default for Shorts).
            duration: Video duration in seconds (6 to 30, default 30).
            resolution: Resolution string ("480p" default).
            mode: Generation mode ("normal", "fun", "spicy").
            nsfw_checker: Boolean flag for NSFW checker.
            poll_interval: Seconds between status polling requests (defaults to GROK_POLL_INTERVAL env or 5).
            timeout: Maximum seconds to wait before timing out (defaults to GROK_POLL_TIMEOUT env or 600).

        Returns:
            Path to the downloaded final.mp4 file.
        """
        import os

        if poll_interval is None:
            poll_interval = int(os.getenv("GROK_POLL_INTERVAL", "5"))
        if timeout is None:
            timeout = int(os.getenv("GROK_POLL_TIMEOUT", "600"))

        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise ValueError("Prompt for Grok Imagine video generator cannot be empty.")

        # Truncate to max 5000 characters if needed
        if len(cleaned_prompt) > 5000:
            logger.warning("[grok_video] Prompt exceeds 5000 chars, truncating.")
            cleaned_prompt = cleaned_prompt[:5000].rstrip()

        logger.info("[grok_video] Creating video task (duration=%ds, res=%s) …", duration, resolution)
        task_id = self.create_task(
            prompt=cleaned_prompt,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            mode=mode,
            nsfw_checker=nsfw_checker,
        )
        logger.info("[grok_video] Task created successfully. Task ID: %s", task_id)

        video_url = self.poll_task_status(task_id, poll_interval=poll_interval, timeout=timeout)
        logger.info("[grok_video] Video generation complete. URL: %s", video_url)

        output_path = run_dir / "final.mp4"
        FileManipulator.ensure_dir(run_dir)
        self.download_file(video_url, output_path)
        logger.info("[grok_video] Video saved → %s", output_path)

        return output_path

    def create_task(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration: int = 30,
        resolution: str = "480p",
        mode: str = "normal",
        nsfw_checker: bool = True,
    ) -> str:
        """Submit a createTask request and return the taskId."""
        payload = {
            "model": self.MODEL_NAME,
            "input": {
                "prompt": prompt.strip(),
                "aspect_ratio": aspect_ratio,
                "mode": mode,
                "duration": duration,
                "resolution": resolution,
                "nsfw_checker": nsfw_checker,
            },
        }

        resp = requests.post(self.CREATE_TASK_URL, headers=self.headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Grok Imagine createTask HTTP error {resp.status_code}: {resp.text}")

        res_json = resp.json()
        code = res_json.get("code")
        if code != 200:
            msg = res_json.get("msg", "Unknown error")
            raise RuntimeError(f"Grok Imagine createTask failed (code {code}): {msg}")

        task_id = res_json.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError(f"Grok Imagine createTask returned no taskId: {res_json}")

        return task_id

    def poll_task_status(self, task_id: str, poll_interval: int = 5, timeout: int = 600) -> str:
        """Poll recordInfo until state is success or fail."""
        start_time = time.time()
        url = f"{self.RECORD_INFO_URL}?taskId={task_id}"

        while time.time() - start_time < timeout:
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code != 200:
                logger.warning("[grok_video] recordInfo HTTP %d, retrying…", resp.status_code)
                time.sleep(poll_interval)
                continue

            res_json = resp.json()
            data = res_json.get("data", {})
            state = data.get("state")

            if state == "success":
                result_json_raw = data.get("resultJson", "{}")
                try:
                    result_json = json.loads(result_json_raw)
                    result_urls = result_json.get("resultUrls", [])
                    if result_urls and len(result_urls) > 0:
                        return result_urls[0]
                except (json.JSONDecodeError, TypeError) as exc:
                    raise RuntimeError(f"Failed to parse Grok Imagine resultJson: {result_json_raw}") from exc

                raise RuntimeError(f"Grok Imagine success response contains no resultUrls: {data}")

            elif state == "fail":
                fail_code = data.get("failCode")
                fail_msg = data.get("failMsg", "Unknown failure")
                raise RuntimeError(f"Grok Imagine task {task_id} failed ({fail_code}): {fail_msg}")

            elif state == "waiting":
                elapsed = int(time.time() - start_time)
                logger.info("[grok_video] Task %s waiting… (%ds elapsed)", task_id, elapsed)

            else:
                logger.info("[grok_video] Task %s state: %s", task_id, state)

            time.sleep(poll_interval)

        raise TimeoutError(f"Grok Imagine task {task_id} timed out after {timeout} seconds.")

    @staticmethod
    def download_file(url: str, dest_path: Path) -> Path:
        """Download file from URL to dest_path."""
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()

        FileManipulator.ensure_dir(dest_path.parent)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return dest_path
