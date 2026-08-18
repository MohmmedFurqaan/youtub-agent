"""
test/test_video_quality_regression.py

Regression test suite for Video Quality Improvement Plan.
Validates VideoPlan structure, props generation, code block payloads,
master timeline precision, and semantic quality gates for key video scenarios:

  1. API request/response flow — diagram + cartoon action + captions
  2. Python implementation — code block + highlighted lines + narration
  3. System architecture — architecture diagram + character explanation
  4. Algorithm explanation — sequence diagram + step-by-step animation
  5. Concept comparison — comparison diagram + captions
"""

import json
from pathlib import Path
import pytest

from src.contracts.video_plan import VideoPlan, validate_video_plan
from src.media.asset_resolver import AssetOrchestrator
from src.pipeline.quality_checks import QualityChecker, QualityCheckError


def _make_scene(
    scene_id: str,
    start_ms: int,
    end_ms: int,
    role: str,
    narration: str,
    on_screen_text: str,
    visual_kind: str,
    query: str,
    template: str | None = None,
    data: dict | None = None,
    code: str | None = None,
    highlight_lines: list[int] | None = None,
    event_type: str = "flow",
    event_action: str = "send",
    cartoon_action: str | None = "idle",
    target: str | None = None,
    from_node: str | None = None,
    to_node: str | None = None,
) -> dict:
    scene_dict = {
        "id": scene_id,
        "story_role": role,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "narration": narration,
        "on_screen_text": on_screen_text,
        "visual": {
            "kind": visual_kind,
            "query": query,
            "required": True,
            "background": "midnight-blue",
        },
        "event": {
            "type": event_type,
            "action": event_action,
            "result": "success",
            "cartoon_action": cartoon_action,
        },
        "transition": "cut",
    }
    if visual_kind == "diagram":
        scene_dict["visual"]["template"] = template or "request-flow"
        scene_dict["visual"]["data"] = data or {
            "nodes": [
                {"id": "n1", "label": "Client", "icon": "smartphone"},
                {"id": "n2", "label": "Server", "icon": "server"},
            ],
            "edges": [{"from": "n1", "to": "n2", "label": "HTTP"}],
        }
        if from_node and to_node:
            scene_dict["event"]["from"] = from_node
            scene_dict["event"]["to"] = to_node
        else:
            scene_dict["event"]["from"] = "n1"
            scene_dict["event"]["to"] = "n2"

    elif visual_kind == "code":
        scene_dict["visual"]["language"] = "python"
        scene_dict["visual"]["code"] = code or "def hello():\n    print('Hello World')\n"
        scene_dict["visual"]["highlight_lines"] = highlight_lines or [2]
        scene_dict["visual"]["title"] = "main.py"
        scene_dict["event"]["target"] = target or "n1"

    return scene_dict


@pytest.fixture
def base_video_plan_dict():
    return {
        "schema_version": "1.0",
        "topic": "System Architecture and API Quality Regression",
        "aspect_ratio": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "target_duration_ms": 30000,
        "voice": "en-US-ChristopherNeural",
        "youtube": {
            "title": "Mastering API Flow and Code Architecture in 30 Seconds",
            "description": "Comprehensive explanation of API request lifecycle and Python implementation.",
            "tags": ["Shorts", "Python", "API", "Architecture", "Engineering"],
            "category_id": "28",
        },
        "scenes": [
            _make_scene(
                "scene-01", 0, 5000, "hook",
                "99 percent of developers get API rate limiting wrong.",
                "API RATE LIMITING", "diagram", "Client sends HTTP request to API gateway",
                template="request-flow", cartoon_action="point"
            ),
            _make_scene(
                "scene-02", 5000, 10000, "problem",
                "Without a rate limiter your backend crashes under traffic bursts.",
                "SERVER OVERLOAD", "diagram", "Multiple clients overwhelm backend server",
                template="comparison", cartoon_action="surprised"
            ),
            _make_scene(
                "scene-03", 10000, 16000, "explanation",
                "Here is the clean Python decorator to limit requests using Redis.",
                "PYTHON LIMITER", "code", "Python rate limiting implementation",
                code="import time\nfrom redis import Redis\n\ndef check_rate(client_id):\n    return redis.incr(client_id) <= 100\n",
                highlight_lines=[4, 5], cartoon_action="think"
            ),
            _make_scene(
                "scene-04", 16000, 24000, "mechanism",
                "The algorithm checks a sliding window counter before forwarding requests.",
                "SLIDING WINDOW", "diagram", "Sliding window algorithm step by step",
                template="sequence", cartoon_action="talk"
            ),
            _make_scene(
                "scene-05", 24000, 30000, "key insight",
                "Protecting your system requires just five lines of clean code.",
                "FIVE LINES CODE", "code", "Clean rate limiter conclusion",
                code="class RateLimiter:\n    def __init__(self, limit=100):\n        self.limit = limit\n",
                highlight_lines=[1, 2], cartoon_action="celebrate"
            ),
        ],
    }


def test_video_plan_schema_validation(base_video_plan_dict):
    """Verify that a plan with both diagrams and code blocks validates cleanly."""
    plan = VideoPlan.model_validate(base_video_plan_dict)
    validate_video_plan(plan)

    assert len(plan.scenes) == 5
    assert plan.scenes[2].visual.kind == "code"
    assert plan.scenes[2].visual.code is not None
    assert plan.scenes[2].event.cartoon_action == "think"
    assert plan.scenes[4].visual.kind == "code"


def test_asset_orchestration_for_code_and_diagrams(tmp_path, base_video_plan_dict):
    """Verify that AssetOrchestrator resolves code blocks and diagrams without failure."""
    plan = VideoPlan.model_validate(base_video_plan_dict)
    run_dir = tmp_path / "test_run"
    run_dir.mkdir()

    orchestrator = AssetOrchestrator(run_dir)
    resolved = orchestrator.resolve_all(plan.scenes)

    # scene-01 (diagram) and scene-03 (code) should produce resolved manifests
    assert "scene-01" in resolved or (run_dir / "assets" / "scene-01" / "asset.json").exists()
    assert "scene-03" in resolved
    assert resolved["scene-03"].kind == "code"
    assert (run_dir / "assets" / "scene-03" / "asset.json").exists()


def test_semantic_quality_gate_checks(tmp_path, base_video_plan_dict):
    """Verify QualityChecker validates code payloads and diagram payloads in props.json."""
    plan = VideoPlan.model_validate(base_video_plan_dict)
    run_dir = tmp_path / "test_run_qa"
    run_dir.mkdir()

    # Save plan.json
    (run_dir / "plan.json").write_text(plan.model_dump_json(), encoding="utf-8")

    # Create dummy props.json matching plan
    props = {
        "audioSrc": "audio/narration.mp3",
        "scenes": [
            {
                "id": s.id,
                "fromFrame": s.start_ms // 33,
                "durationInFrames": (s.end_ms - s.start_ms) // 33,
                "assetSrc": f"assets/{s.id}/asset.txt",
                "assetKind": s.visual.kind,
                "onScreenText": s.on_screen_text,
                "transition": s.transition,
                "event": s.event.model_dump(by_alias=True, exclude_none=True),
                **({
                    "code": {
                        "language": s.visual.language,
                        "code": s.visual.code,
                        "highlightLines": s.visual.highlight_lines,
                        "title": s.visual.title,
                    }
                } if s.visual.kind == "code" else {}),
                **({
                    "diagram": {
                        "template": s.visual.template,
                        "data": s.visual.data or {"nodes": [], "edges": []},
                    }
                } if s.visual.kind == "diagram" else {}),
            }
            for s in plan.scenes
        ],
        "captions": [
            {"text": "Hello", "startMs": 0, "endMs": 1000, "timestampMs": 0, "confidence": 1.0}
        ],
    }
    (run_dir / "props.json").write_text(json.dumps(props), encoding="utf-8")

    # Create scene asset manifests so asset resolution checks pass
    assets_dir = run_dir / "assets"
    for scene in plan.scenes:
        s_dir = assets_dir / scene.id
        s_dir.mkdir(parents=True, exist_ok=True)
        (s_dir / "asset.json").write_text(json.dumps({"source": scene.visual.kind}), encoding="utf-8")

    (run_dir / "captions.json").write_text(json.dumps(props["captions"]), encoding="utf-8")

    # Instantiate QualityChecker and test semantic verification
    checker = QualityChecker(run_dir / "final.mp4", run_dir)
    checker._check_semantic_plan_and_props()
    assert len(checker.errors) == 0
