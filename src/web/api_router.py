"""
src/web/api_router.py — REST and SSE endpoints for YouTube Agent Web UI.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.contracts.video_plan import VideoPlan
from src.pipeline.quality_checks import assert_run_ready_to_upload, QualityCheckError
from src.pipeline.run_pipeline import RunPipeline
from src.utility.file_manipulator import FileManipulator
from src.utility.load_envs import load_all_env
from src.youtube.video_uploader import upload_video

logger = logging.getLogger("yt_agent.web")

router = APIRouter(prefix="/api")

# Global event queues per run_id for real-time progress streaming
_run_event_queues: Dict[str, asyncio.Queue] = {}

openrouter_api_key, openrouter_model_name, kie_api_key, youtube_config = load_all_env()


class CreateRunRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Video topic or prompt")
    model_name: Optional[str] = Field(default=None, description="OpenRouter LLM model name")
    cached_plan_path: Optional[str] = Field(default=None, description="Optional path to cached plan.json")


class UploadRunRequest(BaseModel):
    publish: bool = Field(default=False, description="Make video public on YouTube if True, else Private")


class UpdatePlanRequest(BaseModel):
    plan_data: Dict[str, Any]


def get_data_dir() -> Path:
    return FileManipulator.get_project_root() / "data" / "runs"


def _broadcast_event(run_id: str, stage: str, message: str, status: str = "running", extra: Optional[Dict] = None):
    if run_id in _run_event_queues:
        data = {
            "run_id": run_id,
            "stage": stage,
            "message": message,
            "status": status,
        }
        if extra:
            data.update(extra)
        try:
            _run_event_queues[run_id].put_nowait(data)
        except Exception:
            pass


@router.get("/health")
def get_health_status():
    """Returns status of system, API keys, and environment."""
    return {
        "status": "ok",
        "env": {
            "openrouter_configured": bool(openrouter_api_key),
            "openrouter_model": openrouter_model_name,
            "kie_configured": bool(kie_api_key),
            "youtube_auth_configured": bool(youtube_config and isinstance(youtube_config, dict) and "installed" in youtube_config),
        }
    }


@router.get("/runs")
def list_runs():
    """List all historical video creation runs."""
    data_dir = get_data_dir()
    if not data_dir.exists():
        return []

    runs = []
    for run_dir in sorted(data_dir.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True):
        if not run_dir.is_dir():
            continue
        
        run_json_file = run_dir / "run.json"
        plan_json_file = run_dir / "plan.json"
        final_mp4 = run_dir / "final.mp4"

        run_info = {
            "run_id": run_dir.name,
            "topic": run_dir.name,
            "status": "unknown",
            "has_final_mp4": final_mp4.exists(),
            "has_plan": plan_json_file.exists(),
            "created_at": run_dir.stat().st_ctime,
        }

        if run_json_file.exists():
            try:
                run_data = json.loads(run_json_file.read_text(encoding="utf-8"))
                run_info.update(run_data)
            except Exception:
                pass

        if plan_json_file.exists() and run_info.get("topic") == run_dir.name:
            try:
                plan_data = json.loads(plan_json_file.read_text(encoding="utf-8"))
                if "topic" in plan_data:
                    run_info["topic"] = plan_data["topic"]
            except Exception:
                pass

        runs.append(run_info)

    return runs


@router.get("/runs/{run_id}")
def get_run_details(run_id: str):
    """Get full details, run.json, plan.json, and asset availability for a run."""
    run_dir = get_data_dir() / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    run_json_file = run_dir / "run.json"
    plan_json_file = run_dir / "plan.json"
    final_mp4 = run_dir / "final.mp4"
    narration_mp3 = run_dir / "audio" / "narration.mp3"
    captions_srt = run_dir / "audio" / "captions.srt"
    raw_video = run_dir / "raw" / "final.mp4"

    run_json_data = {}
    if run_json_file.exists():
        try:
            run_json_data = json.loads(run_json_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load run.json for %s: %s", run_id, e)

    plan_json_data = None
    if plan_json_file.exists():
        try:
            plan_json_data = json.loads(plan_json_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load plan.json for %s: %s", run_id, e)

    # Check quality check status
    quality_gate_passed = False
    quality_gate_error = None
    try:
        assert_run_ready_to_upload(run_dir)
        quality_gate_passed = True
    except QualityCheckError as qe:
        quality_gate_error = str(qe)
    except Exception as exc:
        quality_gate_error = str(exc)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "run_data": run_json_data,
        "plan_data": plan_json_data,
        "assets": {
            "final_mp4": f"/api/runs/{run_id}/files/final.mp4" if final_mp4.exists() else None,
            "raw_video": f"/api/runs/{run_id}/files/raw/final.mp4" if raw_video.exists() else None,
            "narration_mp3": f"/api/runs/{run_id}/files/audio/narration.mp3" if narration_mp3.exists() else None,
            "captions_srt": f"/api/runs/{run_id}/files/audio/captions.srt" if captions_srt.exists() else None,
        },
        "quality_gate": {
            "passed": quality_gate_passed,
            "error": quality_gate_error,
        }
    }


def _run_pipeline_worker(run_id: str, topic: str, model_name: str, cached_plan_path: Optional[Path]):
    """Background task executing the video creation pipeline and broadcasting progress events."""
    logger.info("Starting pipeline execution for run_id=%s, topic=%s", run_id, topic)
    _broadcast_event(run_id, "init", "Pipeline initialized", "running")

    try:
        pipeline = RunPipeline(
            topic=topic,
            open_router_model_name=model_name or openrouter_model_name,
            kie_api_key=kie_api_key,
            cached_plan_path=cached_plan_path,
        )

        _broadcast_event(run_id, "plan", "Generating script & VideoPlan with LLM...", "running")
        plan = pipeline._get_plan()
        _broadcast_event(run_id, "plan_complete", "Script & Plan generated successfully", "running", {"plan": plan.model_dump()})

        _broadcast_event(run_id, "ai_video", "Generating 30s AI video via Grok Imagine (KIE.ai)...", "running")
        raw_video_path = pipeline._generate_ai_video(plan)
        _broadcast_event(run_id, "ai_video_complete", "AI Video generated", "running", {"raw_video": str(raw_video_path)})

        _broadcast_event(run_id, "tts", "Synthesizing TTS voiceover audio & SRT subtitles...", "running")
        narration_path, srt_path = pipeline._generate_tts_narration(plan)
        _broadcast_event(run_id, "tts_complete", "TTS narration complete", "running")

        _broadcast_event(run_id, "ffmpeg", "Merging video, audio & burning subtitles via FFmpeg...", "running")
        output_mp4 = pipeline.run_dir / "final.mp4"
        from src.media.ffmpeg_compositor import FFmpegCompositor
        FFmpegCompositor.merge_video_and_audio(
            video_path=raw_video_path,
            audio_path=narration_path,
            output_path=output_mp4,
            srt_path=srt_path,
        )

        _broadcast_event(run_id, "quality", "Running automated quality checks...", "running")
        from src.pipeline.quality_checks import QualityChecker
        QualityChecker(output_mp4, pipeline.run_dir).check_all()

        _broadcast_event(run_id, "done", "Video generation complete & ready for upload!", "completed", {
            "final_mp4": str(output_mp4),
            "run_id": pipeline.run_id
        })

    except Exception as exc:
        logger.exception("Pipeline failed for run %s", run_id)
        _broadcast_event(run_id, "failed", f"Pipeline failed: {str(exc)}", "failed", {"error": str(exc)})


@router.post("/runs/create")
def create_run(req: CreateRunRequest, background_tasks: BackgroundTasks):
    """Initiates a new video creation pipeline."""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    cached_plan = Path(req.cached_plan_path) if req.cached_plan_path else None
    if cached_plan and not cached_plan.exists():
        raise HTTPException(status_code=400, detail=f"Cached plan file not found: {cached_plan}")

    # Generate tentative run_id
    tentative_id, _ = FileManipulator.create_run_directory(topic=req.topic)
    _run_event_queues[tentative_id] = asyncio.Queue()

    background_tasks.add_task(
        _run_pipeline_worker,
        run_id=tentative_id,
        topic=req.topic,
        model_name=req.model_name or openrouter_model_name,
        cached_plan_path=cached_plan,
    )

    return {
        "status": "started",
        "run_id": tentative_id,
        "topic": req.topic,
        "stream_url": f"/api/runs/{tentative_id}/stream",
    }


@router.get("/runs/{run_id}/stream")
async def stream_run_progress(run_id: str):
    """SSE endpoint streaming real-time stage progress updates."""
    if run_id not in _run_event_queues:
        _run_event_queues[run_id] = asyncio.Queue()

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        queue = _run_event_queues[run_id]
        try:
            yield {
                "event": "connected",
                "data": json.dumps({"message": f"Connected to log stream for {run_id}"})
            }
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "progress",
                        "data": json.dumps(data)
                    }
                    if data.get("status") in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    yield {
                        "event": "ping",
                        "data": json.dumps({"ping": True})
                    }
        except asyncio.CancelledError:
            logger.info("Client disconnected from SSE stream for run %s", run_id)

    return EventSourceResponse(event_generator())


@router.put("/runs/{run_id}/plan")
def update_run_plan(run_id: str, req: UpdatePlanRequest):
    """Update or save plan.json for a specific run."""
    run_dir = get_data_dir() / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    plan_file = run_dir / "plan.json"
    FileManipulator.write_json(plan_file, req.plan_data, indent=2)
    return {"status": "success", "message": "plan.json updated successfully"}


@router.post("/runs/{run_id}/upload")
def upload_run_to_youtube(run_id: str, req: UploadRunRequest):
    """Quality check gate & YouTube video upload."""
    run_dir = get_data_dir() / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    try:
        assert_run_ready_to_upload(run_dir)
    except QualityCheckError as qe:
        raise HTTPException(status_code=422, detail=f"Quality check failed: {str(qe)}")

    privacy = "public" if req.publish else "private"

    try:
        upload_video(
            run_id=run_id,
            run_dir=run_dir,
            youtube_config=youtube_config,
            privacy_status=privacy,
        )
        return {
            "status": "success",
            "run_id": run_id,
            "privacy": privacy,
            "message": f"Successfully uploaded video to YouTube ({privacy.upper()})"
        }
    except Exception as exc:
        logger.exception("Upload failed for %s", run_id)
        raise HTTPException(status_code=500, detail=f"YouTube upload failed: {str(exc)}")


@router.get("/runs/{run_id}/files/{file_path:path}")
def serve_run_file(run_id: str, file_path: str):
    """Serve asset files (videos, audio, images, subtitles) from run directory."""
    run_dir = get_data_dir() / run_id
    target_file = (run_dir / file_path).resolve()

    # Ensure path stays within run_dir for security
    if not str(target_file).startswith(str(run_dir.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden file access")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(target_file)
