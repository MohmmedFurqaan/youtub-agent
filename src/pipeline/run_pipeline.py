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
            })
            # If this is a Remotion-native diagram, include the typed diagram data
            if scene.visual.kind == "diagram":
                # Include template and data as-is (validated by VideoPlan)
                diagram_data = dict(scene.visual.data)

                # Synthesize an animationTimeline when the LLM/plan did not provide one.
                # This creates conservative, semantic events (enter, cursor, click, move-packet)
                # that span the scene duration and reference node ids from the diagram.
                if not diagram_data.get("animationTimeline"):
                    nodes = diagram_data.get("nodes", [])
                    edges = diagram_data.get("edges", [])
                    timeline: list[dict] = []

                    # entrance
                    timeline.append({"atMs": 0, "durationMs": min(800, max(200, int(duration_ms * 0.08))), "type": "enter"})

                    # If nodes available, add a cursor+click on the first node
                    if nodes:
                        first_node = nodes[0]["id"]
                        cursor_at = timeline[-1]["atMs"] + timeline[-1]["durationMs"] // 2
                        timeline.append({"atMs": cursor_at, "durationMs": 500, "type": "cursor-move", "target": first_node})
                        timeline.append({"atMs": cursor_at + 400, "durationMs": 250, "type": "click", "target": first_node})

                    # If edges exist, split remaining time among them to move packets sequentially
                    remaining_ms = duration_ms - (timeline[-1]["atMs"] + timeline[-1]["durationMs"])
                    if remaining_ms > 300 and edges:
                        per_edge = max(300, int(remaining_ms / len(edges)))
                        start = timeline[-1]["atMs"] + timeline[-1]["durationMs"] + 50
                        for i, e in enumerate(edges):
                            at = start + i * per_edge
                            duration_ev = min(per_edge - 50, max(300, int(per_edge * 0.9)))
                            ev = {
                                "atMs": int(at),
                                "durationMs": int(duration_ev),
                                "type": "move-packet",
                                "from": e.get("from"),
                                "to": e.get("to"),
                                # optional label based on edge label
                                "text": e.get("label") or "",
                            }
                            timeline.append(ev)
                            # highlight node on arrival
                            timeline.append({"atMs": int(at + duration_ev - 120), "durationMs": 220, "type": "highlight-node", "target": e.get("to")})

                    diagram_data["animationTimeline"] = timeline

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
        }

        props_path = self.run_dir / "props.json"
        _write_json(props_path, props)
        logger.info("[pipeline] props.json written → %s", props_path)
        return props_path

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
        # Prefer invoking the local remotion binary if present to avoid
        # npx/npm attempting to fetch packages from the registry.
        local_remotion = _RENDERER_DIR / "node_modules" / ".bin" / "remotion"
        # Debug: log whether the local remotion candidate exists and is executable
        try:
            exists = local_remotion.exists()
            is_file = local_remotion.is_file()
            mode = oct(local_remotion.stat().st_mode & 0o777) if exists else "n/a"
        except Exception:
            exists = False
            is_file = False
            mode = "err"
        logger.info("[pipeline] local remotion candidate: %s exists=%s is_file=%s mode=%s", local_remotion, exists, is_file, mode)
        if local_remotion.exists():
            cmd = [str(local_remotion.resolve()), "render", "ShortVideo", str(output_mp4.resolve()), f"--props={props_path.resolve()}"]
        else:
            # Fallback to npx when local binary isn't available
            cmd = ["npx", "remotion", "render", "ShortVideo", str(output_mp4.resolve()), f"--props={props_path.resolve()}"]

        logger.info("[pipeline] Render command: %s", " ".join(cmd))

        subprocess.run(
            cmd,
            cwd=str(_RENDERER_DIR),
            check=True,  # raises CalledProcessError on failure
            text=True,
        )
        logger.info("[pipeline] Remotion render complete → %s", output_mp4)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
