"""
test/test_props_builder.py

Tests that run_pipeline._build_props() produces the correct props.json
structure for Remotion, given a known VideoPlan and resolved assets.

Run with:  uv run pytest test/test_props_builder.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.contracts.video_plan import Scene, VisualAsset, VideoPlan, YouTubeMetadata
from src.media.asset_resolver import ResolvedAsset
from src.media.tts_generator import TTSResult
from src.media.captions import CaptionRecord


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_plan() -> VideoPlan:
    return VideoPlan.model_validate({
        "topic": "How APIs work",
        "youtube": {
            "title": "How APIs Work",
            "description": "30-second explanation.",
            "tags": ["API", "Tech", "Shorts"],
        },
        "scenes": [
            {
                "id": "scene-01", "start_ms": 0, "end_ms": 8000,
                "narration": "Your phone sends a request.", "on_screen_text": "REQUEST SENT",
                "visual": {"kind": "diagram", "query": "phone to API flow"},
            },
            {
                "id": "scene-02", "start_ms": 8000, "end_ms": 15000,
                "narration": "The API is the middleman.", "on_screen_text": "THE MIDDLEMAN",
                "visual": {"kind": "diagram", "query": "API gateway middleman"},
            },
            {
                "id": "scene-03", "start_ms": 15000, "end_ms": 22000,
                "narration": "The server processes it.", "on_screen_text": "SERVER RESPONDS",
                "visual": {"kind": "diagram", "query": "server processing request"},
            },
            {
                "id": "scene-04", "start_ms": 22000, "end_ms": 30000,
                "narration": "You get a response instantly.", "on_screen_text": "DATA RETURNED",
                "visual": {"kind": "diagram", "query": "response data returned to phone"},
            },
        ],
    })


def _make_resolved_assets(plan: VideoPlan, run_dir: Path) -> dict[str, ResolvedAsset]:
    results = {}
    for scene in plan.scenes:
        asset_dir = run_dir / "assets" / scene.id
        asset_dir.mkdir(parents=True, exist_ok=True)
        asset_file = asset_dir / "asset.svg"
        asset_file.write_text("<svg/>")
        results[scene.id] = ResolvedAsset(
            scene_id=scene.id,
            local_path=asset_file,
            kind="diagram",
            source="diagram",
        )
    return results


def _make_tts_result(run_dir: Path) -> TTSResult:
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    mp3 = audio_dir / "narration.mp3"
    mp3.write_bytes(b"\xff\xfb")  # minimal MP3 header
    captions: list[CaptionRecord] = [
        {"text": "Your", "startMs": 0, "endMs": 200, "timestampMs": 0, "confidence": 1.0},
        {"text": "phone", "startMs": 200, "endMs": 450, "timestampMs": 200, "confidence": 1.0},
    ]
    return TTSResult(mp3_path=mp3, duration_ms=29500, captions=captions)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestPropsBuilder:
    """Test _build_props() indirectly by calling it through RunPipeline."""

    def test_props_structure(self, tmp_path):
        """props.json must contain audioSrc, scenes, captions."""
        from src.pipeline.run_pipeline import RunPipeline

        plan = _make_plan()
        resolved = _make_resolved_assets(plan, tmp_path)
        tts = _make_tts_result(tmp_path)

        # Construct a RunPipeline and call _build_props directly
        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline._build_props(plan, resolved, tts)

        assert props_path.exists()
        props = json.loads(props_path.read_text())

        assert "audioSrc" in props
        assert "scenes" in props
        assert "captions" in props
        assert len(props["scenes"]) == 4

    def test_scene_frame_windows(self, tmp_path):
        """Scenes must have correct fromFrame and durationInFrames (@ 30 fps)."""
        from src.pipeline.run_pipeline import RunPipeline

        plan = _make_plan()
        resolved = _make_resolved_assets(plan, tmp_path)
        tts = _make_tts_result(tmp_path)

        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline._build_props(plan, resolved, tts)
        props = json.loads(props_path.read_text())
        scenes = props["scenes"]

        # scene-01: 0 → 8000 ms = 0 → 240 frames
        assert scenes[0]["fromFrame"] == 0
        assert scenes[0]["durationInFrames"] == 240

        # scene-02: 8000 → 15000 ms = 240 → 210 frames
        assert scenes[1]["fromFrame"] == 240
        assert scenes[1]["durationInFrames"] == 210

    def test_asset_src_paths(self, tmp_path):
        """assetSrc must be relative to public/runs/<run-id>/."""
        from src.pipeline.run_pipeline import RunPipeline

        plan = _make_plan()
        resolved = _make_resolved_assets(plan, tmp_path)
        tts = _make_tts_result(tmp_path)

        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline._build_props(plan, resolved, tts)
        props = json.loads(props_path.read_text())

        for scene_prop in props["scenes"]:
            assert scene_prop["assetSrc"].startswith(f"runs/{pipeline.run_id}/")
            assert scene_prop["assetSrc"].endswith("asset.svg")

    def test_audio_src_path(self, tmp_path):
        from src.pipeline.run_pipeline import RunPipeline

        plan = _make_plan()
        resolved = _make_resolved_assets(plan, tmp_path)
        tts = _make_tts_result(tmp_path)

        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline._build_props(plan, resolved, tts)
        props = json.loads(props_path.read_text())

        assert props["audioSrc"] == f"runs/{pipeline.run_id}/audio/narration.mp3"

    def test_captions_preserved(self, tmp_path):
        from src.pipeline.run_pipeline import RunPipeline

        plan = _make_plan()
        resolved = _make_resolved_assets(plan, tmp_path)
        tts = _make_tts_result(tmp_path)

        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline._build_props(plan, resolved, tts)
        props = json.loads(props_path.read_text())

        assert props["captions"] == tts.captions
        assert props["captions"][0]["text"] == "Your"


def _make_pipeline(tmp_path: Path):
    """Create a RunPipeline with its run_dir redirected to tmp_path."""
    import uuid
    from src.pipeline.run_pipeline import RunPipeline, _DATA_DIR
    from unittest.mock import patch

    run_id = str(uuid.uuid4())
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)

    pipeline = object.__new__(RunPipeline)
    pipeline.topic = "How APIs work"
    pipeline.model_name = "test-model"
    pipeline.cached_plan_path = None
    pipeline.run_id = run_id
    pipeline.run_dir = run_dir
    return pipeline
