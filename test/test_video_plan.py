"""
test/test_video_plan.py

Unit tests for VideoPlan Pydantic contract and validate_video_plan().
"""

import pytest
from src.contracts.video_plan import VideoPlan, validate_video_plan


def _make_valid_plan_dict() -> dict:
    return {
        "topic": "How an API request works",
        "hook": "Ever wondered what happens when you press Enter?",
        "voice_script": "When you hit Enter, your browser resolves DNS, connects via TLS, and sends an HTTP payload to the server.",
        "motion_prompt": "A cinematic 30-second visual animation showing data packets traveling through neon light highways into a server gateway.",
        "youtube": {
            "title": "How an API Request Works in 30 Seconds",
            "description": "Watch what happens behind the scenes when an API request is sent!",
            "tags": ["api", "tech", "programming"],
            "category_id": "28",
        },
    }


def test_valid_video_plan():
    plan_dict = _make_valid_plan_dict()
    plan = VideoPlan.model_validate(plan_dict)
    validate_video_plan(plan)

    assert plan.topic == "How an API request works"
    assert plan.hook.startswith("Ever wondered")
    assert len(plan.motion_prompt) > 20


def test_invalid_motion_prompt_too_long():
    plan_dict = _make_valid_plan_dict()
    plan_dict["motion_prompt"] = "A" * 5001

    with pytest.raises(Exception):
        VideoPlan.model_validate(plan_dict)


def test_empty_fields_raise_error():
    plan_dict = _make_valid_plan_dict()
    plan_dict["hook"] = "   "

    with pytest.raises(Exception):
        VideoPlan.model_validate(plan_dict)
