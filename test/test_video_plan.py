"""
test/test_video_plan.py

Unit tests for VideoPlan Pydantic contract and validate_video_plan().
"""

import pytest
from src.contracts.video_plan import VideoPlan, validate_video_plan


def _make_valid_plan_dict() -> dict:
    return {
        "topic": "How an API request works",
        "hook": "Your browser sends an HTTP request every time you click a button.",
        "voice_script": (
            "Your browser sends an HTTP request every time you click a button. "
            "Here is what happens behind the scenes. First, DNS resolves the domain name into an IP address. "
            "Next, a secure TLS handshake opens an encrypted connection to the server. "
            "Finally, the API endpoint processes your JSON payload and sends back a response in milliseconds. "
            "That's how modern web applications communicate seamlessly across the internet."
        ),
        "motion_prompt": (
            "Cinematic 30-second shot. Camera starts with a close-up of a cursor clicking a glowing button on a laptop screen. "
            "The camera perspective zooms into the screen into a digital highway of light particles representing data. "
            "A luminous packet races through a neon server room, reaching a metallic gateway structure where processing lights up."
        ),
        "youtube": {
            "title": "How an API Request Works in 30 Seconds",
            "description": "Here is what happens behind the scenes when your browser sends an HTTP request to an API.",
            "tags": ["api", "tech", "programming", "backend", "webdev"],
            "category_id": "28",
        },
    }


def test_valid_video_plan():
    plan_dict = _make_valid_plan_dict()
    plan = VideoPlan.model_validate(plan_dict)
    validate_video_plan(plan)

    assert plan.topic == "How an API request works"
    assert len(plan.voice_script.split()) >= 40
    assert len(plan.motion_prompt) > 20


def test_banned_ai_phrase_raises_error():
    plan_dict = _make_valid_plan_dict()
    plan_dict["hook"] = "Ever wondered how an API request works under the hood?"
    plan = VideoPlan.model_validate(plan_dict)

    with pytest.raises(ValueError, match="generic AI phrase"):
        validate_video_plan(plan)


def test_script_too_short_raises_error():
    plan_dict = _make_valid_plan_dict()
    plan_dict["voice_script"] = "APIs are fast. They send data between client and server instantly."
    plan = VideoPlan.model_validate(plan_dict)

    with pytest.raises(ValueError, match="too short"):
        validate_video_plan(plan)


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
