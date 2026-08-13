"""
Seedance 2.5 API Client

Thin HTTP transport layer for the Seedance 2.5 video generation API.
Handles authentication, request serialization, and response parsing
for the two-step workflow: createTask → recordInfo.

API Reference: docs/seedance-api.md
"""

import json
import http.client
from src.utility.logging_config import setup_logging


BASE_HOST = "api.kie.ai"
MODEL_ID = "bytedance/seedance-2-5"

CREATE_TASK_PATH = "/api/v1/jobs/createTask"
RECORD_INFO_PATH = "/api/v1/jobs/recordInfo"


class SeedanceClient:
    """HTTP client for the Seedance 2.5 API (api.kie.ai).

    Responsibilities:
        - Serialize requests and parse responses for createTask / recordInfo.
        - Manage the Bearer token authentication header.
        - Provide clean return types (str for task IDs, dict for status).

    This class has NO knowledge of prompts, scripts, scenes, or files.
    """

    def __init__(self, api_key: str):
        """Initialize the client with a KIE API key.

        Args:
            api_key: Bearer token for api.kie.ai authentication.
        """
        if not api_key:
            raise ValueError("api_key is required for SeedanceClient")

        self._api_key = api_key
        self._logger = setup_logging(__name__)


    def create_task(
        self,
        prompt: str,
        duration: int = 30,
        aspect_ratio: str = "9:16",
        resolution: str = "720p",
        output_format: str = "mp4",
        generate_audio: bool = True,
        reference_image_urls: list[str] | None = None,
        reference_video_urls: list[str] | None = None,
        reference_audio_urls: list[str] | None = None,
        first_frame_url: str | None = None,
        last_frame_url: str | None = None,
        return_last_frame: bool = False,
        nsfw_checker: bool = True,
        callback_url: str | None = None,
    ) -> str:
        """Submit a video generation task to the Seedance 2.5 API.

        Args:
            prompt:               Text description for the video (max 30000 chars).
            duration:             Video duration in seconds (1–30, default 30).
            aspect_ratio:         Output aspect ratio (default "9:16").
            resolution:           Output resolution — "480p" or "720p" (default "720p").
            output_format:        Output format — "mp4" or "mov" (default "mp4").
            generate_audio:       Generate AI-synced audio (default True).
            reference_image_urls: Optional list of reference image URLs.
            reference_video_urls: Optional list of reference video URLs.
            reference_audio_urls: Optional list of reference audio URLs.
            first_frame_url:      Optional first frame image URL.
            last_frame_url:       Optional last frame image URL.
            return_last_frame:    Return the last frame of the video (default False).
            nsfw_checker:         Enable NSFW content filter (default True).
            callback_url:         Optional callback URL for completion notification.

        Returns:
            The taskId string for polling via query_task().

        Raises:
            RuntimeError: If the API returns a non-200 response or missing taskId.
        """
        input_params = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": output_format,
            "generate_audio": generate_audio,
            "return_last_frame": return_last_frame,
            "nsfw_checker": nsfw_checker,
        }

        # Optional media references
        if reference_image_urls:
            input_params["reference_image_urls"] = reference_image_urls
        if reference_video_urls:
            input_params["reference_video_urls"] = reference_video_urls
        if reference_audio_urls:
            input_params["reference_audio_urls"] = reference_audio_urls
        if first_frame_url:
            input_params["first_frame_url"] = first_frame_url
        if last_frame_url:
            input_params["last_frame_url"] = last_frame_url

        payload = {
            "model": MODEL_ID,
            "input": input_params,
        }

        if callback_url:
            payload["callBackUrl"] = callback_url

        self._logger.info(
            "[seedance] Creating task: duration=%ds, aspect_ratio=%s, resolution=%s",
            duration, aspect_ratio, resolution,
        )

        resp = self._request("POST", CREATE_TASK_PATH, payload)

        if resp.get("code") != 200:
            raise RuntimeError(
                f"Seedance createTask failed: code={resp.get('code')} msg={resp.get('msg')}"
            )

        task_id = resp.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError(f"Seedance createTask returned no taskId: {resp}")

        self._logger.info("[seedance] Task created: taskId=%s", task_id)
        return task_id

    def query_task(self, task_id: str) -> dict:
        """Query the status of a generation task.

        Args:
            task_id: The taskId returned by create_task().

        Returns:
            Full API response dict with structure:
            {
                "code": 200,
                "msg": "success",
                "data": {
                    "taskId": "...",
                    "state": "waiting" | "success" | "fail",
                    "resultJson": "...",
                    "failCode": ...,
                    "failMsg": ...,
                    ...
                }
            }
        """
        path = f"{RECORD_INFO_PATH}?taskId={task_id}"
        return self._request("GET", path)


    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        """Execute an HTTP request against api.kie.ai and return parsed JSON."""
        conn = http.client.HTTPSConnection(BASE_HOST)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = json.dumps(payload) if payload else None

        try:
            conn.request(method, path, body, headers)
            res = conn.getresponse()
            raw = res.read().decode("utf-8")
        finally:
            conn.close()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._logger.error("[seedance] Non-JSON response from %s: %s", path, raw[:500])
            return {"code": 500, "msg": "Non-JSON response", "raw": raw}
