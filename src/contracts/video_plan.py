"""
src/contracts/video_plan.py

Pydantic v2 contract for the Grok Imagine AI Video pipeline.
OpenRouter model produces a JSON object matching this schema.
"""

from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, Field

# Common cliché AI opening phrases to reject for human-like natural tone
BANNED_AI_PATTERNS = [
    r"\bever wondered\b",
    r"\bin this video\b",
    r"\bin today'?s video\b",
    r"\bwelcome back\b",
    r"\bdelve into\b",
    r"\bunlock the secrets?\b",
    r"\bin the fast-paced world\b",
    r"\bmastering the art of\b",
]


class YouTubeMetadata(BaseModel):
    title: str = Field(..., min_length=5)
    description: str = Field(..., min_length=10)
    tags: list[str] = Field(..., min_length=3)
    category_id: str = "28"


class VideoPlan(BaseModel):
    """Root contract for Grok Imagine Text-To-Video execution."""

    schema_version: Literal["1.0"] = "1.0"
    topic: str = Field(..., min_length=3)
    hook: str = Field(..., min_length=5)
    voice_script: str = Field(..., min_length=10)
    motion_prompt: str = Field(..., min_length=20, max_length=5000)
    youtube: YouTubeMetadata


def validate_video_plan(plan: VideoPlan) -> None:
    """Validate structural constraints and anti-AI naturalness rules for VideoPlan.

    Raises:
        ValueError: If any validation or naturalness rule fails.
    """
    if not plan.topic.strip():
        raise ValueError("Topic cannot be empty.")
    if not plan.hook.strip():
        raise ValueError("Hook cannot be empty.")
    if not plan.voice_script.strip():
        raise ValueError("Voice script cannot be empty.")

    # Check for cliché AI opening patterns in hook and voice script
    combined_text = f"{plan.hook} {plan.voice_script}".lower()
    for pattern in BANNED_AI_PATTERNS:
        if re.search(pattern, combined_text):
            clean_pattern = pattern.replace(r"\b", "").replace("'", "")
            raise ValueError(
                f"Voice script/hook contains generic AI phrase ('{clean_pattern}'). "
                "Output must be natural, human-written, and free of AI clichés."
            )

    # Word count check for natural 30-second speaking cadence (approx 40-85 words)
    words = plan.voice_script.strip().split()
    word_count = len(words)
    if word_count < 40:
        raise ValueError(
            f"Voice script is too short ({word_count} words). "
            "Script must be between 40 and 85 words for a natural 30-second narration."
        )
    if word_count > 85:
        raise ValueError(
            f"Voice script is too long ({word_count} words). "
            "Script must be between 40 and 85 words for a natural 30-second narration."
        )

    prompt = plan.motion_prompt.strip()
    if not prompt:
        raise ValueError("Motion prompt cannot be empty.")
    if len(prompt) > 5000:
        raise ValueError(f"Motion prompt length ({len(prompt)}) exceeds 5000 characters maximum.")
