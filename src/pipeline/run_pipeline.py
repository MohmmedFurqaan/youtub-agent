"""
src/pipeline/run_pipeline.py

Orchestrates the complete video creation pipeline in strict order:

  1.  create run_id + data/runs/<run-id>/ directories
  2.  generate or load+validate VideoPlan → plan.json
  3.  resolve visual assets for every scene
  4.  generate narration MP3 + captions.json
  5.  build props.json (Remotion input)
  6.  copy assets to video-renderer/public/runs/<run-id>/
  7.  invoke Remotion renderer via subprocess
  8.  run quality checks on the output MP4
  9.  write run.json (status, paths, errors)
  10. clean video-renderer/public/runs/<run-id>/ after render

The pipeline NEVER uploads.  Upload is a separate command.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.contracts.video_plan import VideoPlan
from src.media.asset_resolver import AssetOrchestrator, ResolvedAsset
from src.media.tts_generator import NarrationGenerator, TTSResult
from src.model.service.prompt_agent import VideoScriptGeneratorAgent
from src.pipeline.quality_checks import QualityChecker, QualityCheckError
from src.utility.logging_config import setup_logging

logger = setup_logging()

# Project root (two levels up from this file -> the `yt-agent` folder)
# Using parents[2] ensures `_RENDERER_DIR` points to the sibling
# `video-renderer` inside the same repository tree.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RENDERER_DIR = _PROJECT_ROOT / "video-renderer"
_DATA_DIR = _PROJECT_ROOT / "data" / "runs"


class RunPipeline:
    """Executes one full create run from topic to final.mp4."""

    def __init__(
        self,
        topic: str,
        open_router_model_name: str,
        cached_plan_path: Optional[Path] = None,
    ) -> None:
        self.topic = topic
        self.model_name = open_router_model_name
        self.cached_plan_path = cached_plan_path

        self.run_id = str(uuid.uuid4())
        self.run_dir = _DATA_DIR / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[pipeline] Run ID: %s", self.run_id)
        logger.info("[pipeline] Run dir: %s", self.run_dir)

    # ── Public ────────────────────────────────────────────────────────────────

    def execute(self) -> Path:
        """Run all pipeline stages.

        Returns:
            Path to the rendered final.mp4.

        Raises:
            RuntimeError, QualityCheckError, subprocess.CalledProcessError
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

            # Stage 3: assets
            resolved_assets = self._resolve_assets(plan)
            run_json["paths"]["assets"] = str(self.run_dir / "assets")

            # Stage 4: TTS + captions
            tts_result = self._generate_narration(plan)
            run_json["paths"]["audio"] = str(tts_result.mp3_path)
            run_json["paths"]["captions"] = str(self.run_dir / "captions.json")

            # Stage 5: props.json
            props_path = self._build_props(plan, resolved_assets, tts_result)
            run_json["paths"]["props"] = str(props_path)

            # Stage 6: copy assets to public/
            public_run_dir = self._copy_assets_to_public(tts_result.mp3_path, resolved_assets)

            # Stage 7: render
            output_mp4 = self.run_dir / "final.mp4"
            self._render(props_path, output_mp4)
            run_json["paths"]["final_mp4"] = str(output_mp4)

            # Stage 8: quality checks
            QualityChecker(output_mp4, self.run_dir).check_all()

            # Stage 9: success
            run_json["status"] = "ready_to_upload"
            run_json["completed_at"] = _now_iso()
            logger.info("[pipeline] ✓ Render complete → %s", output_mp4)

        except Exception as exc:
            run_json["status"] = "failed"
            run_json["errors"].append(str(exc))
            run_json["failed_at"] = _now_iso()
            logger.error("[pipeline] ✗ Run failed: %s", exc)
            raise

        finally:
            # Stage 9: write run.json regardless of success/failure
            _write_json(self.run_dir / "run.json", run_json)

           

        return self.run_dir / "final.mp4"

    # ── Stage implementations ─────────────────────────────────────────────────

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

    def _resolve_assets(self, plan: VideoPlan) -> dict[str, ResolvedAsset]:
        """Stage 3: resolve a visual asset for every scene."""
        logger.info("[pipeline] Resolving assets for %d scenes …", len(plan.scenes))
        orchestrator = AssetOrchestrator(self.run_dir)
        return orchestrator.resolve_all(plan.scenes)

    def _generate_narration(self, plan: VideoPlan) -> TTSResult:
        """Stage 4: generate one narration.mp3 + captions.json."""
        logger.info("[pipeline] Generating narration …")
        generator = NarrationGenerator(plan, self.run_dir)
        return generator.generate()

    def _build_props(
        self,
        plan: VideoPlan,
        resolved_assets: dict[str, ResolvedAsset],
        tts_result: TTSResult,
    ) -> Path:
        """Stage 5: assemble props.json for Remotion.

        Paths inside props.json are relative to
        video-renderer/public/runs/<run-id>/ so that staticFile() works.
        """
        fps = plan.fps
        run_id = self.run_id

        scene_props = []
        cumulative_frame = 0
        for scene in plan.scenes:
            duration_ms = scene.end_ms - scene.start_ms
            duration_frames = round(duration_ms / 1000 * fps)

            asset = resolved_assets.get(scene.id)
            asset_filename = asset.local_path.name if asset else "asset.svg"
            asset_src = f"runs/{run_id}/{scene.id}/{asset_filename}"
            asset_kind = scene.visual.kind

            scene_props.append({
                "id": scene.id,
                "fromFrame": cumulative_frame,
                "durationInFrames": duration_frames,
                "assetSrc": asset_src,
                "assetKind": asset_kind,
                "onScreenText": scene.on_screen_text,
                "transition": scene.transition,
                "background": scene.visual.background,
                "storyRole": getattr(scene, "story_role", None) or scene.id.split("-")[-1],
                "event": scene.event.model_dump(by_alias=True, exclude_none=True),
            })

            if scene.visual.kind == "code":
                scene_props[-1]["code"] = {
                    "language": scene.visual.language or "python",
                    "code": scene.visual.code or "",
                    "highlightLines": scene.visual.highlight_lines or [],
                    "title": scene.visual.title or "",
                    "focusRange": scene.visual.focus_range,
                }

            if scene.visual.kind == "diagram":
                diagram_data = dict(scene.visual.data or {})

                animation_timeline = self._resolve_animation_timeline(
                    scene,
                    duration_ms,
                )

                diagram_data["animationTimeline"] = animation_timeline

                scene_props[-1]["diagram"] = {
                    "template": scene.visual.template,
                    "data": diagram_data,
                }
            cumulative_frame += duration_frames

        # Audio path inside public/
        audio_src = f"runs/{run_id}/audio/narration.mp3"

        props = {
            "title": plan.youtube.title,
            "audioSrc": audio_src,
            "scenes": scene_props,
            "captions": tts_result.captions,
            "musicSrc": "music/tech_ambient.mp3",
        }

        props_path = self.run_dir / "props.json"
        _write_json(props_path, props)
        logger.info("[pipeline] props.json written → %s", props_path)
        return props_path

    def _resolve_animation_timeline(
        self,
        scene,
        duration_ms: int,
    ) -> list[dict]:
        """
        Convert the semantic SceneEvent into renderer-friendly
        animation timeline events.

        The LLM describes WHAT happens.
        This resolver decides the deterministic timeline.
        """

        event = scene.event
        event_type = event.type

        timeline: list[dict] = []

        

        timeline.append({
            "atMs": 0,
            "durationMs": min(500, duration_ms // 8),
            "type": "enter",
        })


        if event_type == "flow":
            if not event.from_ or not event.to_:
                raise ValueError(
                    f"{scene.id}: flow event requires from and to"
                )

            start_ms = min(700, duration_ms // 5)
            available = max(800, duration_ms - start_ms - 400)

            timeline.append({
                "atMs": start_ms,
                "durationMs": available,
                "type": "move-packet",
                "from": event.from_,
                "to": event.to_,
                "text": event.label or "",
            })

            timeline.append({
                "atMs": start_ms + available - 100,
                "durationMs": 300,
                "type": "highlight-node",
                "target": event.to_,
            })

        

        elif event_type == "response":
            if not event.from_ or not event.to_:
                raise ValueError(
                    f"{scene.id}: response event requires from and to"
                )

            start_ms = min(700, duration_ms // 5)
            available = max(800, duration_ms - start_ms - 400)

            timeline.append({
                "atMs": start_ms,
                "durationMs": available,
                "type": "move-packet",
                "from": event.from_,
                "to": event.to_,
                "text": event.label or "response",
            })

            timeline.append({
                "atMs": start_ms + available - 100,
                "durationMs": 300,
                "type": "highlight-node",
                "target": event.to_,
            })



        elif event_type == "reveal":
            if not event.target:
                raise ValueError(
                    f"{scene.id}: reveal event requires target"
                )

            start_ms = min(700, duration_ms // 4)

            timeline.append({
                "atMs": start_ms,
                "durationMs": min(700, duration_ms // 4),
                "type": "reveal-node",
                "target": event.target,
                "text": event.label or "",
            })

            timeline.append({
                "atMs": start_ms + 700,
                "durationMs": 300,
                "type": "highlight-node",
                "target": event.target,
            })

        

        elif event_type == "comparison":
            timeline.append({
                "atMs": min(600, duration_ms // 6),
                "durationMs": min(700, duration_ms // 5),
                "type": "comparison-reveal",
                "left": event.left or "",
                "right": event.right or "",
            })



        elif event_type == "sequence":
            steps = event.steps or []

            if not steps:
                raise ValueError(
                    f"{scene.id}: sequence event requires steps"
                )

            start_ms = min(600, duration_ms // 6)
            available = max(1000, duration_ms - start_ms - 300)
            per_step = max(300, available // len(steps))

            for index, step in enumerate(steps):
                timeline.append({
                    "atMs": start_ms + index * per_step,
                    "durationMs": min(per_step - 50, 700),
                    "type": "sequence-step",
                    "index": index,
                    "text": step,
                })



        elif event_type == "metric":
            timeline.append({
                "atMs": min(500, duration_ms // 6),
                "durationMs": min(1800, duration_ms // 2),
                "type": "metric-change",
                "label": event.label or "",
                "result": event.result,
            })

        else:
            raise ValueError(
                f"{scene.id}: unsupported event type {event_type}"
            )

        return timeline
    
    def _copy_assets_to_public(
        self,
        mp3_path: Path,
        resolved_assets: dict[str, ResolvedAsset],
    ) -> Path:
        """Stage 6: copy run assets to video-renderer/public/runs/<run-id>/."""
        public_run_dir = _RENDERER_DIR / "public" / "runs" / self.run_id
        public_run_dir.mkdir(parents=True, exist_ok=True)

        # Copy narration audio
        audio_dest = public_run_dir / "audio"
        audio_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp3_path, audio_dest / "narration.mp3")

        # Copy each scene asset
        for scene_id, asset in resolved_assets.items():
            dest_dir = public_run_dir / scene_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset.local_path, dest_dir / asset.local_path.name)

        logger.info("[pipeline] Assets copied to public/ → %s", public_run_dir)
        return public_run_dir

    def _render(self, props_path: Path, output_mp4: Path) -> None:
        """Stage 7: invoke Remotion renderer via subprocess."""
        logger.info("[pipeline] Starting Remotion render …")
        local_remotion = _RENDERER_DIR / "node_modules" / ".bin" / "remotion"
        local_remotion_cmd = _RENDERER_DIR / "node_modules" / ".bin" / "remotion.cmd"

        use_shell = False
        if local_remotion_cmd.exists():
            cmd = [str(local_remotion_cmd.resolve()), "render", "ShortVideo", str(output_mp4.resolve()), f"--props={props_path.resolve()}"]
        elif local_remotion.exists():
            cmd = [str(local_remotion.resolve()), "render", "ShortVideo", str(output_mp4.resolve()), f"--props={props_path.resolve()}"]
        else:
            npx_bin = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
            cmd = [npx_bin, "remotion", "render", "ShortVideo", str(output_mp4.resolve()), f"--props={props_path.resolve()}"]
            use_shell = sys.platform == "win32"

        logger.info("[pipeline] Render command: %s", " ".join(cmd))

        subprocess.run(
            cmd,
            cwd=str(_RENDERER_DIR),
            check=True,
            text=True,
            shell=use_shell,
        )
        logger.info("[pipeline] Remotion render complete → %s", output_mp4)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
