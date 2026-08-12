from src.utility.load_envs import load_all_env
from src.utility.logging_config import setup_logging
from src.utility.save_response import SaveLlmResponse
import json
import http.client
import time
import subprocess
import urllib.request
from pathlib import Path
import requests


class VideoGeneratorAgent:

    # Only use the cheapest model tier to conserve credits.
    MODEL = "veo3_lite"

    # Polling config for waiting on task completion
    POLL_INTERVAL_SECONDS = 30
    POLL_MAX_ATTEMPTS = 40  # 40 x 30s = 20 min max wait

    def __init__(self, script: dict, KIE_API_KEY: str, script_id: str = None):
        '''Initialize the video generator agent.
        Args:
            script (dict): The structured video script containing
                           visual_bible, scenes, video metadata, etc.
            KIE_API_KEY (str): The Bearer token for api.kie.ai.
            script_id (str): The unique ID from llm_response.json used for
                             folder naming and metadata tracking.
        '''
        self.script = script
        self.KIE_API_KEY = KIE_API_KEY
        self.script_id = script_id
        self.logger = setup_logging()

        # Stores the taskId chain: scene_number -> taskId
        self.task_chain: dict[int, str] = {}

        # Project root for file paths
        self.project_root = Path(__file__).resolve().parents[3]

        # Directory layout:
        #   data/metadata/scene/          -> individual scene clips
        #   data/metadata/{id}_video/     -> final stitched video
        self.scene_dir = self.project_root / "data" / "metadata" / "scene"
        self.video_dir = self.project_root / "data" / "metadata" / f"{self.script_id}_video"
        self.scene_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)


    def build_initial_prompt(self, visual_bible: dict, scene: dict) -> str:
        '''Build the full prompt for Scene 1 (veo_initial).
        Includes the visual bible so the model anchors on style from
        the very first frame.
        '''
        return f"""\
            VISUAL BIBLE — FOLLOW THESE RULES THROUGHOUT THE VIDEO

            Visual Style:
            {visual_bible["visual_style"]}

            Environment:
            {visual_bible["environment"]}

            Lighting:
            {visual_bible["lighting"]}

            Color Palette:
            {", ".join(visual_bible["color_palette"])}

            Camera Style:
            {visual_bible["camera_style"]}

            Objects:
            {", ".join(visual_bible["objects"])}

            Continuity Rules:
            {chr(10).join(f"- {rule}" for rule in visual_bible["continuity_rules"])}

            SCENE {scene["scene_number"]}

            Purpose:
            {scene["purpose"]}

            Duration:
            {scene["duration"]} seconds

            Visual Prompt:
            {scene["background_prompt"]}

            Continuation:
            {scene["continuation_instruction"]}
            """

    @staticmethod
    def build_extension_prompt(scene: dict) -> str:
        '''Build the prompt for extension scenes (veo_extension).
        Lighter than the initial prompt — the visual bible is already
        baked into the base video.
        '''
        return f"""\
        SCENE {scene["scene_number"]}

        Purpose:
        {scene["purpose"]}

        Duration:
        {scene["duration"]} seconds

        Visual Prompt:
        {scene["background_prompt"]}

        Continuation:
        {scene["continuation_instruction"]}
        """

    def _make_request(self, method: str, path: str, payload: dict | None = None) -> dict:
        '''Low-level helper to talk to api.kie.ai and return parsed JSON.'''
        conn = http.client.HTTPSConnection("api.kie.ai")
        headers = {
            'Authorization': f'Bearer {self.KIE_API_KEY}',
            'Content-Type': 'application/json'
        }
        body = json.dumps(payload) if payload else None
        conn.request(method, path, body, headers)
        res = conn.getresponse()
        raw = res.read().decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.logger.error(f"Non-JSON response from {path}: {raw[:500]}")
            return {"code": 500, "msg": "Non-JSON response", "raw": raw}

    def _base_agent_initializer(
        self,
        prompt: str,
        generation_type: str,
        aspect_ratio: str = "9:16",
        enable_translation: bool = True,
        duration: int = 8,
        model: str = "lite",
        watermark: str = "codewith__motiwala",
    ) -> dict:
        '''Generate an initial video clip via /api/v1/veo/generate.
        Args:
            prompt: The full visual prompt for the scene.
            generation_type: e.g. "video".
            aspect_ratio: Default 9:16 (shorts).
            enable_translation: Let the API translate if needed.
            duration: Clip duration in seconds.
            model: Model tier — lite | fast | quality.
            watermark: Watermark text overlay.
        Returns:
            Parsed JSON response from the API.
        '''
        payload = {
            "prompt": prompt,
            "model": model,
            "watermark": watermark,
            "aspect_ratio": aspect_ratio,
            "enableFallback": False,
            "enableTranslation": enable_translation,
            "generationType": generation_type,
        }
        self.logger.info(f"[generate] Sending initial request with model={model}")
        return self._make_request("POST", "/api/v1/veo/generate", payload)

    def _extend_video(
        self,
        task_id: str,
        prompt: str,
        model: str = "lite",
        seeds: int | None = None,
        watermark: str = "codewith__motiwala",
    ) -> dict:
        '''Extend an existing video via /api/v1/veo/extend.
        Args:
            task_id: The taskId of the video to extend from.
            prompt: Description of how to extend the video.
            model: Model tier — lite | fast | quality.
            seeds: Optional seed for reproducibility (10000-99999).
            watermark: Watermark text overlay.
        Returns:
            Parsed JSON response from the API.
        '''
        payload = {
            "taskId": task_id,
            "prompt": prompt,
            "model": model,
        }
        if watermark:
            payload["watermark"] = watermark
        if seeds is not None:
            payload["seeds"] = max(10000, min(99999, seeds))

        self.logger.info(f"[extend] Extending taskId={task_id} with model={model}")
        return self._make_request("POST", "/api/v1/veo/extend", payload)

    def _poll_task_status(self, task_id: str) -> dict:
        '''Poll /api/v1/jobs/recordInfo until the task completes or fails.
        Returns the final status response dict.

        API Response format (from docs):
        {
            "code": 505,
            "msg": "success",
            "data": {
                "taskId": "...",
                "state": "success",
                "resultJson": "{\"resultUrls\":[\"https://...\"]}",
                "progress": 45,
                ...
            }
        }
        '''
        self.logger.info(f"[poll] Waiting for taskId={task_id} ...")
        for attempt in range(1, self.POLL_MAX_ATTEMPTS + 1):
            time.sleep(self.POLL_INTERVAL_SECONDS)
            resp = self._make_request("GET", f"/api/v1/jobs/recordInfo?taskId={task_id}")

            # _make_request already returns parsed JSON dict
            data = resp.get("data", {})
            if not isinstance(data, dict):
                data = {}

            state = str(data.get("state", "")).lower()
            progress = data.get("progress", "N/A")

            self.logger.info(
                f"[poll] attempt {attempt}/{self.POLL_MAX_ATTEMPTS}  "
                f"taskId={task_id}  state={state}  progress={progress}  "
                f"response_keys={list(data.keys())}"
            )

            # Parse resultJson if present (it's a JSON string)
            result_urls = []
            result_json_str = data.get("resultJson", "")
            if result_json_str and isinstance(result_json_str, str):
                try:
                    result_data = json.loads(result_json_str)
                    result_urls = result_data.get("resultUrls", [])
                except (json.JSONDecodeError, TypeError):
                    pass

            if state == "success" or result_urls:
                self.logger.info(
                    f"[poll] Task {task_id} completed. state={state} "
                    f"result_urls={result_urls}"
                )
                # Attach parsed result URLs to the response for easy access
                if "data" in resp and isinstance(resp["data"], dict):
                    resp["data"]["_parsed_result_urls"] = result_urls
                return resp
            elif state in ("failed", "error", "rejected"):
                fail_msg = data.get("failMsg", "unknown")
                fail_code = data.get("failCode", "unknown")
                self.logger.error(
                    f"[poll] Task {task_id} failed: state={state} "
                    f"failCode={fail_code} failMsg={fail_msg}"
                )
                return resp

        self.logger.error(f"[poll] Task {task_id} timed out after {self.POLL_MAX_ATTEMPTS} attempts.")
        return {"code": 408, "msg": "Polling timed out", "taskId": task_id}

    def _download_scene_video(
        self,
        task_id: str,
        scene_num: int,
        status_resp: dict
    ) -> Path | None:

        data = status_resp.get("data", {})

        # Already parsed by _poll_task_status()
        result_urls = data.get("_parsed_result_urls", [])

        if not result_urls:
            self.logger.error(
                f"[download] No result URL found for Scene {scene_num}"
            )
            return None

        video_url = result_urls[0]

        scene_file = self.scene_dir / f"scene_{scene_num}.mp4"

        self.logger.info(
            f"[download] Downloading Scene {scene_num} -> {scene_file}"
        )
        self.logger.info(f"[download] URL: {video_url}")

        
        try:
            response = requests.get(
                video_url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
                stream=True,
                timeout=120,
            )

            self.logger.info(
                f"[download] HTTP status: {response.status_code}"
            )

            response.raise_for_status()

            with open(scene_file, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

            self.logger.info(
                f"[download] Scene {scene_num} saved: "
                f"{scene_file} ({scene_file.stat().st_size} bytes)"
            )

            return scene_file

        except requests.RequestException as e:
            self.logger.error(
                f"[download] Failed to download Scene {scene_num}: {e}"
            )
            return None
            
    def stitch_scenes(self) -> Path | None:
        '''Use FFmpeg to concatenate all scene clips into one final video.

        Reads scene files from data/metadata/scene/ in order and writes
        the stitched output to data/metadata/{script_id}_video/.

        Returns:
            Path to the final stitched video, or None on failure.
        '''
        # Collect scene files in order
        scene_files = sorted(self.scene_dir.glob("scene_*.mp4"))

        if not scene_files:
            self.logger.error("[stitch] No scene files found to stitch.")
            return None

        self.logger.info(f"[stitch] Stitching {len(scene_files)} scene(s): {[f.name for f in scene_files]}")

        # Build FFmpeg concat file list
        concat_list_path = self.scene_dir / "concat_list.txt"
        with open(concat_list_path, "w") as f:
            for scene_file in scene_files:
                # FFmpeg requires forward slashes and escaped single quotes
                f.write(f"file '{scene_file.resolve()}'\n")

        output_path = self.video_dir / f"{self.script_id}_final.mp4"

        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_list_path),
                    "-c", "copy",
                    output_path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                self.logger.error(f"[stitch] FFmpeg failed:\n{result.stderr}")
                # Fallback: re-encode if stream copy fails (codec mismatch)
                self.logger.info("[stitch] Retrying with re-encode...")
                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", str(concat_list_path),
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "23",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        str(output_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    self.logger.error(f"[stitch] Re-encode also failed:\n{result.stderr}")
                    return None

            self.logger.info(f"[stitch] Final video saved: {output_path} ({output_path.stat().st_size} bytes)")
            return output_path

        except FileNotFoundError:
            self.logger.error("[stitch] FFmpeg not found. Please install FFmpeg.")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error("[stitch] FFmpeg timed out.")
            return None

    def generate_full_video(self) -> dict:
        '''Walk through every scene in the script, generate video clips,
        download each scene, and stitch them together with FFmpeg.

        Returns a dict with:
            task_chain: scene_number -> taskId
            scene_files: scene_number -> file path
            final_video: path to stitched video (or None)
        '''
        visual_bible = self.script["visual_bible"]
        scenes = self.script["scenes"]
        aspect_ratio = self.script.get("video", {}).get("aspect_ratio", "9:16")

        previous_task_id = None
        scene_files: dict[int, str] = {}

        for scene in scenes:
            scene_num = scene["scene_number"]
            scene_type = scene.get("scene_type", "veo_extension")
            duration = scene.get("duration", 8)

            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"Processing Scene {scene_num}  type={scene_type}")
            self.logger.info(f"{'='*50}")

            # Scene 1: initial generation
            if scene_type == "veo_initial" or previous_task_id is None:
                prompt = self.build_initial_prompt(visual_bible, scene)
                resp = self._base_agent_initializer(
                    prompt=prompt,
                    generation_type="video",
                    aspect_ratio=aspect_ratio,
                    duration=duration,
                    model=self.MODEL,
                )

                if resp.get("code") != 200 or not resp.get("data", {}).get("taskId"):
                    self.logger.error(f"Scene {scene_num}: Failed to generate video. Response: {resp}")
                    return {"error": f"Failed to generate Scene {scene_num}", "response": resp}

                task_id = resp["data"]["taskId"]
                self.logger.info(f"Scene {scene_num}: Initial generation taskId = {task_id}")

            # Scenes 2+: extension
            else:
                prompt = self.build_extension_prompt(scene)
                resp = self._extend_video(
                    task_id=previous_task_id,
                    prompt=prompt
                )

                if resp.get("code") != 200 or not resp.get("data", {}).get("taskId"):
                    self.logger.error(f"Scene {scene_num}: Failed to extend video. Response: {resp}")
                    return {"error": f"Failed to extend Scene {scene_num}", "response": resp}

                task_id = resp["data"]["taskId"]
                self.logger.info(f"Scene {scene_num}: Extension taskId = {task_id}")

            # Wait for the task to finish before extending further
            status_resp = self._poll_task_status(task_id)
            final_status = status_resp.get("data", {}).get("state", "").lower()

            if final_status not in ("completed", "success", "done"):
                self.logger.error(
                    f"Scene {scene_num}: Task {task_id} did not complete "
                    f"(status={final_status}). Stopping chain."
                )
                break

            # Download the scene video
            scene_path = self._download_scene_video(task_id, scene_num, status_resp)
            if scene_path:
                scene_files[scene_num] = str(scene_path)

            # Record and advance the chain
            self.task_chain[scene_num] = task_id
            previous_task_id = task_id
            self.logger.info(f"Scene {scene_num}: Done. taskId={task_id}")

        self.logger.info(f"\nTask chain: {self.task_chain}")

        # Stitch all downloaded scenes into one final video
        final_video = None
        if scene_files:
            final_video = self.stitch_scenes()

        return {
            "task_chain": self.task_chain,
            "scene_files": scene_files,
            "final_video": str(final_video) if final_video else None,
        }