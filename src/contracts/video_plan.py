"""
src/contracts/video_plan.py

Pydantic v2 contract for the Grok Imagine AI Video pipeline.
NVIDIA Nemotron / OpenRouter produces a JSON object matching this schema.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


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
    """Validate structural constraints for VideoPlan.

    Raises:
        ValueError: If any validation rule fails.
    """
    if not plan.topic.strip():
        raise ValueError("Topic cannot be empty.")
    if not plan.hook.strip():
        raise ValueError("Hook cannot be empty.")
    if not plan.voice_script.strip():
        raise ValueError("Voice script cannot be empty.")
    
    prompt = plan.motion_prompt.strip()
    if not prompt:
        raise ValueError("Motion prompt cannot be empty.")
    if len(prompt) > 5000:
        raise ValueError(f"Motion prompt length ({len(prompt)}) exceeds 5000 characters maximum.")
