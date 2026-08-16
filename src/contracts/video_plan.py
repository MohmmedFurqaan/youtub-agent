"""
src/contracts/video_plan.py

Pydantic v2 source-of-truth contract for the Remotion video pipeline.
NVIDIA Nemotron produces a JSON blob matching this schema; every
downstream stage (asset resolver, TTS, Remotion renderer) reads from it.

No text-to-video API fields are accepted — veo_prompt, extension_prompt,
video_prompt, reference_image_urls, shots, production are all rejected.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# create the story literals
StoryRole = Literal[
    "hook",
    "problem",
    "explanation",
    "mechanism",
    "key insight"
]

class SceneEvent(BaseModel):
    type: Literal[
        "flow",
        "response",
        "reveal",
        "comparison",
        "sequence",
        "metric",
    ]

    action: str

    from_: str | None = Field(default=None, alias="from")
    to_: str | None = Field(default=None, alias="to")

    label: str | None = None
    result: str

    left: str | None = None
    right: str | None = None
    steps: list[str] | None = None
    target: str | None = None

    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }

# ── Sub-models ────────────────────────────────────────────────────────────────


class VisualAsset(BaseModel):
    """Describes the visual asset required for a scene.

    kind:
        "diagram"        — SVG/text+icon layout drawn by Remotion directly.
        "image"          — Still image (Pollinations, if USE_POLLINATIONS_STILL=true).
        "stock_video"    — Licensed local stock video file.
        "screen_capture" — Screen-recording clip from the local library.
    query:
        Provider-neutral description used by the asset resolver.
    required:
        If True, the pipeline fails when this asset cannot be resolved.
    background:
        Optional color treatment for the scene's background. Helps Remotion
        create more dynamic visuals for each diagram or still image.
    """

    kind: Literal["stock_video", "image", "diagram", "screen_capture"]
    query: str = Field(..., min_length=5)
    required: bool = True
    background: str | None = None

    # Diagram-specific (optional unless kind == 'diagram')
    template: str | None = None
    data: dict | None = None


class Scene(BaseModel):
    """One scene in the video.

    id:           Stable within a run, e.g. "scene-01".
    start_ms:     Start time in milliseconds from video start.
    end_ms:       End time in milliseconds (exclusive).
    narration:    Exactly what the narrator says. ≤ 20 words.
    on_screen_text: 2–5 word overlay keyword/phrase shown on screen.
    visual:       Asset descriptor (resolved by the media layer).
    transition:   How this scene follows the previous one.
    """

    

    id: str = Field(..., pattern=r"^scene-\d{2}$")
    story_role: StoryRole
    start_ms: int = Field(..., ge=0)
    end_ms: int = Field(..., gt=0)
    narration: str
    on_screen_text: str
    visual: VisualAsset
    event: SceneEvent
    transition: Literal["cut", "fade", "slide"] = "cut"
    

    @model_validator(mode="after")
    def _end_after_start(self) -> "Scene":
        if self.end_ms <= self.start_ms:
            raise ValueError(
                f"{self.id}: end_ms ({self.end_ms}) must be greater than start_ms ({self.start_ms})"
            )
        duration_ms = self.end_ms - self.start_ms
        if not (4000 <= duration_ms <= 10000):
            raise ValueError(
                f"{self.id}: duration {duration_ms} ms is outside the 4–10 second range"
            )
        words = len(self.on_screen_text.strip().split())
        if not (2 <= words <= 5):
            raise ValueError(
                f"{self.id}: on_screen_text has {words} word(s); expected 2–5"
            )
        return self


    @model_validator(mode="after")
    def _validate_visual(self) -> "Scene":
        # If visual.kind is diagram, ensure template and data follow expectations
        if self.visual.kind == "diagram":
            templates = {
                "request-flow",
                "architecture-layers",
                "sequence",
                "comparison",
                "timeline",
                "concept-card",
                "metric-chart",
            }
            if not self.visual.template:
                raise ValueError(f"{self.id}: diagram template is required for kind=diagram")
            if self.visual.template not in templates:
                raise ValueError(f"{self.id}: unsupported diagram template '{self.visual.template}'")

            # Validate basic structure of data
            data = self.visual.data or {}
            nodes = data.get("nodes")
            edges = data.get("edges")
            if not isinstance(nodes, list) or not isinstance(edges, list):
                raise ValueError(f"{self.id}: diagram data must include 'nodes' and 'edges' arrays")

            # Supported icon set (must match iconRegistry in TS)
            supported_icons = {
                "smartphone",
                "monitor",
                "server",
                "database",
                "cloud",
                "user",
                "lock",
                "shield",
                "globe",
                "code",
                "gitBranch",
                "message",
                "zap",
                "activity",
            }

            for n in nodes:
                if not isinstance(n, dict):
                    raise ValueError(f"{self.id}: each node must be an object")
                icon = n.get("icon")
                if icon and icon not in supported_icons:
                    raise ValueError(f"{self.id}: unsupported icon name '{icon}' in node {n.get('id')}")

        return self


class YouTubeMetadata(BaseModel):
    title: str = Field(..., min_length=5)
    description: str = Field(..., min_length=10)
    tags: list[str] = Field(..., min_length=3)
    category_id: str = "28"


class VideoPlan(BaseModel):
    """Root contract.  This is the single source of truth for a render run."""

    schema_version: Literal["1.0"] = "1.0"
    topic: str = Field(..., min_length=5)
    aspect_ratio: Literal["9:16"] = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    target_duration_ms: int = 30000
    voice: str = "en-US-ChristopherNeural"
    youtube: YouTubeMetadata
    scenes: list[Scene]

    @model_validator(mode="before")
    @classmethod
    def _reject_legacy_fields(cls, data: dict) -> dict:
        """Fail fast if any legacy Veo/Seedance/Grok field is present."""
        legacy = {
            "veo_prompt",
            "extension_prompt",
            "video_prompt",
            "reference_image_urls",
            "shots",
            "production",
        }
        found = legacy & set(data.keys())
        if found:
            raise ValueError(
                f"Legacy field(s) not accepted in VideoPlan: {sorted(found)}"
            )
        return data

    @model_validator(mode="after")
    def _validate_events(self) -> "VideoPlan":
        for scene in self.scenes:
            if scene.event is None:
                raise ValueError(
                    f"{scene.id}: event is required"
                )

        return self


# ── Validation helper ─────────────────────────────────────────────────────────


def validate_video_plan(plan: VideoPlan) -> None:
    """Run structural checks that Pydantic field validators cannot express.

    Raises:
        ValueError: with a human-readable message describing the problem.
    """
    scenes = plan.scenes

    # 1. Scene count
    if len(scenes) != 5:
        raise ValueError(
            f"VideoPlan must have exactly 5 scenes; got {len(scenes)}"
        )

    # 2. First scene starts at 0
    if scenes[0].start_ms != 0:
        raise ValueError(
            f"First scene must start at 0 ms; got {scenes[0].start_ms}"
        )

    # 3. No gaps or overlaps — each scene starts exactly where the previous ended
    for i in range(1, len(scenes)):
        expected_start = scenes[i - 1].end_ms
        actual_start = scenes[i].start_ms
        if actual_start != expected_start:
            raise ValueError(
                f"{scenes[i].id}: expected start_ms={expected_start} "
                f"(end of {scenes[i-1].id}), got {actual_start}"
            )

    # 4. Last scene ends at exactly 30 000 ms
    if scenes[-1].end_ms != 30000:
        raise ValueError(
            f"Last scene must end at 30000 ms; got {scenes[-1].end_ms}"
        )
