"""
test/test_video_plan.py

Unit tests for VideoPlan Pydantic contract and validate_video_plan().
Run with:  uv run pytest test/test_video_plan.py -v
"""

import numpy as np
import pytest

from src.contracts.video_plan import (
    Scene,
    VisualAsset,
    VideoPlan,
    YouTubeMetadata,
    validate_video_plan,
)
from src.model.service.prompt_agent import VideoScriptGeneratorAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_youtube() -> dict:
    return {
        "title": "How APIs Work",
        "description": "A 30-second explanation of API request flow.",
        "tags": ["API", "Tech", "Shorts"],
        "category_id": "22",
    }


def _make_scenes(count: int = 4) -> list[dict]:
    """Build `count` gapless scenes that total exactly 30 000 ms."""
    assert count in (4, 5), "fixture only supports 4 or 5 scenes"
    if count == 4:
        boundaries = [0, 8000, 15000, 22000, 30000]
    else:
        boundaries = [0, 6000, 12000, 18000, 24000, 30000]

    scenes = []
    for i in range(count):
        scenes.append({
            "id": f"scene-0{i + 1}",
            "start_ms": boundaries[i],
            "end_ms": boundaries[i + 1],
            "narration": "Your phone sends a request to the API.",
            "on_screen_text": "REQUEST SENT",
            "visual": {
                "kind": "diagram",
                "query": "phone-to-API flow, dark style",
                "template": "request-flow",
                "data": {
                    "nodes": [{"id": "a", "label": "Client", "icon": "smartphone"},{"id": "b", "label": "API", "icon": "server"}],
                    "edges": [{"from": "a", "to": "b", "label": "request"}],
                    "highlightEdge": 0,
                },
            },
            "transition": "cut",
        })
    return scenes


def _make_valid_plan(scene_count: int = 4) -> dict:
    return {
        "topic": "How an API request works",
        "youtube": _make_youtube(),
        "scenes": _make_scenes(scene_count),
    }


# ── Valid input ───────────────────────────────────────────────────────────────


class TestValidPlan:
    def test_four_scenes(self):
        plan = VideoPlan.model_validate(_make_valid_plan(4))
        validate_video_plan(plan)
        assert len(plan.scenes) == 4

    def test_five_scenes(self):
        plan = VideoPlan.model_validate(_make_valid_plan(5))
        validate_video_plan(plan)
        assert len(plan.scenes) == 5

    def test_default_fields(self):
        plan = VideoPlan.model_validate(_make_valid_plan())
        assert plan.width == 1080
        assert plan.height == 1920
        assert plan.fps == 30
        assert plan.target_duration_ms == 30000
        assert plan.voice == "en-US-ChristopherNeural"
        assert plan.aspect_ratio == "9:16"

    def test_visual_background_is_supported(self):
        data = _make_valid_plan()
        data["scenes"][0]["visual"]["background"] = "midnight-blue"
        plan = VideoPlan.model_validate(data)
        assert plan.scenes[0].visual.background == "midnight-blue"

    def test_narration_is_padded_to_target_duration(self):
        from src.media.tts_generator import NarrationGenerator

        short_audio = np.zeros(24000, dtype=np.float32)
        padded = NarrationGenerator._pad_audio_to_duration(short_audio, 30000, 24000)

        assert len(padded) == 720000
        assert padded.shape[0] == 720000

    def test_scene_duration_in_range(self):
        """Each scene in the 4-scene fixture is 7–8 s — within 4–10 s."""
        plan = VideoPlan.model_validate(_make_valid_plan())
        for scene in plan.scenes:
            duration = scene.end_ms - scene.start_ms
            assert 4000 <= duration <= 10000

    def test_on_screen_text_word_count(self):
        plan = VideoPlan.model_validate(_make_valid_plan())
        for scene in plan.scenes:
            words = len(scene.on_screen_text.strip().split())
            assert 2 <= words <= 5


# ── Gap / Overlap ─────────────────────────────────────────────────────────────


class TestGapOverlap:
    def test_gap_between_scenes(self):
        data = _make_valid_plan()
        # Introduce a 500 ms gap after scene-01
        data["scenes"][1]["start_ms"] = 8500  # was 8000
        plan = VideoPlan.model_validate(data)
        with pytest.raises(ValueError, match="expected start_ms=8000"):
            validate_video_plan(plan)

    def test_overlap_between_scenes(self):
        data = _make_valid_plan()
        # scene-02 starts 1 s early → overlaps scene-01
        data["scenes"][1]["start_ms"] = 7000  # was 8000
        data["scenes"][1]["end_ms"] = 15000
        plan = VideoPlan.model_validate(data)
        with pytest.raises(ValueError, match="expected start_ms=8000"):
            validate_video_plan(plan)


# ── Non-30-second total ───────────────────────────────────────────────────────


class TestDuration:
    def test_total_not_30_seconds(self):
        data = _make_valid_plan()
        # Last scene ends at 29 000 instead of 30 000
        data["scenes"][-1]["end_ms"] = 29000
        plan = VideoPlan.model_validate(data)
        with pytest.raises(ValueError, match="30000"):
            validate_video_plan(plan)

    def test_first_scene_not_at_zero(self):
        data = _make_valid_plan()
        data["scenes"][0]["start_ms"] = 500
        plan = VideoPlan.model_validate(data)
        with pytest.raises(ValueError, match="start at 0"):
            validate_video_plan(plan)

    def test_too_few_scenes(self):
        """validate_video_plan() must catch fewer than 4 scenes."""
        data = _make_valid_plan()
        # Keep only 3 scenes, preserve their individual durations (all valid)
        # but the total won't be 30 s — validate_video_plan checks count first.
        data["scenes"] = data["scenes"][:3]
        # Force last scene to end at 30000 with a valid duration (≤10s)
        data["scenes"][-1]["end_ms"] = data["scenes"][-1]["start_ms"] + 8000
        # Manually set it so Pydantic accepts the scene, then check count
        # scene-03: 15000 → 23000 (8s valid), total not 30000 but that's OK —
        # validate_video_plan raises on count before checking total.
        plan = VideoPlan.model_validate(data)
        with pytest.raises(ValueError, match="4–5 scenes"):
            validate_video_plan(plan)


# ── Legacy fields ─────────────────────────────────────────────────────────────


class TestLegacyFields:
    @pytest.mark.parametrize("field", [
        "veo_prompt",
        "extension_prompt",
        "video_prompt",
        "reference_image_urls",
        "shots",
        "production",
    ])
    def test_rejects_legacy_field(self, field: str):
        data = _make_valid_plan()
        data[field] = "should be rejected"
        with pytest.raises(Exception, match=field):
            VideoPlan.model_validate(data)


# ── Scene-level field validation ──────────────────────────────────────────────


class TestSceneValidation:
    def test_on_screen_text_too_short(self):
        data = _make_valid_plan()
        data["scenes"][0]["on_screen_text"] = "API"  # 1 word
        with pytest.raises(ValueError, match="2–5"):
            VideoPlan.model_validate(data)

    def test_on_screen_text_too_long(self):
        data = _make_valid_plan()
        data["scenes"][0]["on_screen_text"] = "one two three four five six"  # 6 words
        with pytest.raises(ValueError, match="2–5"):
            VideoPlan.model_validate(data)

    def test_scene_duration_too_short(self):
        data = _make_valid_plan()
        data["scenes"][0]["end_ms"] = 2000  # 2 s — below 4 s minimum
        with pytest.raises(ValueError, match="4–10 second"):
            VideoPlan.model_validate(data)

    def test_scene_duration_too_long(self):
        data = _make_valid_plan()
        data["scenes"][0]["end_ms"] = 20000  # 20 s — above 10 s maximum
        with pytest.raises(ValueError, match="4–10 second"):
            VideoPlan.model_validate(data)


def test_invalid_diagram_template_is_normalized_to_kind_diagram():
    plan = {
        "schema_version": "1.0",
        "topic": "How APIs work",
        "youtube": _make_youtube(),
        "scenes": [],
    }

    for i, end_ms in enumerate([8000, 15000, 22000, 30000], start=1):
        start_ms = 0 if i == 1 else plan["scenes"][-1]["end_ms"]
        plan["scenes"].append({
            "id": f"scene-0{i}",
            "start_ms": start_ms,
            "end_ms": end_ms,
            "narration": "The client sends a request.",
            "on_screen_text": "REQUEST SENT",
            "visual": {
                "kind": "comparison",
                "query": "phone sends request to API gateway",
                "template": "comparison",
                "data": {"nodes": [{"id": "a", "label": "Client", "icon": "smartphone"}], "edges": []},
            },
            "transition": "cut",
        })

    normalized = VideoScriptGeneratorAgent._repair_invalid_visual_schema(plan)
    assert normalized["scenes"][0]["visual"]["kind"] == "diagram"
    assert normalized["scenes"][0]["visual"]["template"] == "comparison"

    validated = VideoPlan.model_validate(normalized)
    validate_video_plan(validated)
