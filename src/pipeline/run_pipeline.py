"""
src/pipeline/run_pipeline.py

Orchestrates the complete video creation pipeline via Grok Imagine AI Video + TTS Voiceover + Captions:

  1. Create readable run_id + data/runs/<run-id>/ directory
  2. Generate or load VideoPlan → plan.json
  3. Invoke Grok Imagine API to generate 30s AI video → raw/final.mp4
  4. Synthesize TTS voiceover audio & SRT subtitles → audio/narration.mp3, audio/captions.srt
  5. Merge AI video + TTS audio + burned captions via FFmpeg → final.mp4
  6. Run quality checks on final.mp4
  7. Write run.json (status, paths, errors)

The pipeline NEVER uploads. Upload is a separate command.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.contracts.video_plan import VideoPlan
from src.media.ffmpeg_compositor import FFmpegCompositor
from src.media.grok_video_generator import GrokVideoGenerator
from src.media.tts_generator import TTSGenerator
from src.model.service.prompt_agent import VideoScriptGeneratorAgent
from src.pipeline.quality_checks import QualityChecker
from src.utility.file_manipuator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()

_DATA_DIR = FileManipulator.get_project_root() / "data" / "runs"


class RunPipeline:
    """Executes one full create run from topic to final.mp4 via Grok Imagine + TTS + Subtitles."""

    def __init__(
        self,
        topic: str,
        open_router_model_name: str,
        kie_api_key: str,
        cached_plan_path: Optional[Path] = None,
    ) -> None:
        self.topic = topic
        self.model_name = open_router_model_name
        self.kie_api_key = kie_api_key
        self.cached_plan_path = cached_plan_path

        self.run_id, self.run_dir = FileManipulator.create_run_directory(topic=topic)

        logger.info("[pipeline] Readable Run ID: %s", self.run_id)
        logger.info("[pipeline] Run dir: %s", self.run_dir)

    def execute(self) -> Path:
        """Run all pipeline stages.

        Returns:
            Path to the rendered final.mp4 containing video + voiceover audio + burned captions.

        Raises:
            RuntimeError, QualityCheckError
        """
        run_json: dict = {
            "run_id": self.run_id,
            "topic": self.topic,
            "started_at": _now_iso(),
            "status": "running",
            "paths": {},
            "errors": [],
        }

        try:
            # Stage 2: plan
            plan = self._get_plan()
            run_json["paths"]["plan"] = str(self.run_dir / "plan.json")

            # Stage 3: Grok Imagine AI Video Generation
            raw_video_path = self._generate_ai_video(plan)
            run_json["paths"]["raw_video"] = str(raw_video_path)

            # Stage 4: TTS Voiceover Narration & Subtitles
            narration_path, srt_path = self._generate_tts_narration(plan)
            run_json["paths"]["narration"] = str(narration_path)
            if srt_path:
                run_json["paths"]["subtitles"] = str(srt_path)

            # Stage 5: Merge Audio, Video & Burn Subtitles via FFmpeg
            output_mp4 = self.run_dir / "final.mp4"
            FFmpegCompositor.merge_video_and_audio(
                video_path=raw_video_path,
                audio_path=narration_path,
                output_path=output_mp4,
                srt_path=srt_path,
            )
            run_json["paths"]["final_mp4"] = str(output_mp4)

            # Stage 6: quality checks
            QualityChecker(output_mp4, self.run_dir).check_all()

            # Stage 7: success
            run_json["status"] = "ready_to_upload"
            run_json["completed_at"] = _now_iso()
            logger.info("[pipeline] ✓ Video generation complete → %s", output_mp4)

        except Exception as exc:
            run_json["status"] = "failed"
            run_json["errors"].append(str(exc))
            run_json["failed_at"] = _now_iso()
            logger.error("[pipeline] ✗ Run failed: %s", exc)
            raise

        finally:
            FileManipulator.write_json(self.run_dir / "run.json", run_json, indent=2)

        return self.run_dir / "final.mp4"

    def _get_plan(self) -> VideoPlan:
        """Stage 2: generate or load the VideoPlan."""
        if self.cached_plan_path:
            logger.info("[pipeline] Loading cached plan from %s", self.cached_plan_path)
            return VideoScriptGeneratorAgent.load_plan_from_file(self.cached_plan_path)

        agent = VideoScriptGeneratorAgent(
            topic=self.topic,
            open_router_model_name=self.model_name,
        )
        return agent.generate(self.run_dir)

    def _generate_ai_video(self, plan: VideoPlan) -> Path:
        """Stage 3: generate 30s raw video using Grok Imagine API."""
        logger.info("[pipeline] Initiating Grok Imagine Text-To-Video API generation …")
        generator = GrokVideoGenerator(self.kie_api_key)
        raw_video_dir = FileManipulator.ensure_dir(self.run_dir / "raw")
        return generator.generate_video(
            prompt=plan.motion_prompt,
            run_dir=raw_video_dir,
            aspect_ratio="9:16",
            duration=30,
            resolution="480p",
            mode="normal",
        )

    def _generate_tts_narration(self, plan: VideoPlan) -> tuple[Path, Path | None]:
        """Stage 4: synthesize TTS narration audio and SRT subtitles from voice_script."""
        logger.info("[pipeline] Generating TTS voiceover narration & subtitles …")
        audio_dir = FileManipulator.ensure_dir(self.run_dir / "audio")
        output_mp3 = audio_dir / "narration.mp3"
        output_srt = audio_dir / "captions.srt"
        generator = TTSGenerator()
        return generator.generate_narration_and_subtitles(plan.voice_script, output_mp3, output_srt)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
