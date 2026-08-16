"""
src/media/captions.py

Build Remotion-compatible caption records from edge-tts word events.

Caption record format (matches @remotion/captions Caption type):
    {
        "text":        str,    # word or phrase
        "startMs":     int,    # milliseconds from video start
        "endMs":       int,
        "timestampMs": int,    # same as startMs (Remotion convention)
        "confidence":  float   # 1.0 from TTS; lower from transcription
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


class CaptionRecord(TypedDict):
    text: str
    startMs: int
    endMs: int
    timestampMs: int
    confidence: float


def build_captions_from_word_events(
    word_events: list[dict],
) -> list[CaptionRecord]:
    """Convert edge-tts word boundary events into caption records.

    edge-tts yields events like:
        {"type": "WordBoundary", "offset": 12500000, "duration": 4375000, "text": "Hello"}
    offset and duration are in 100-nanosecond units (divide by 10 000 for ms).

    Args:
        word_events: List of word boundary dicts from edge-tts.

    Returns:
        List of CaptionRecord dicts sorted by startMs.
    """
    captions: list[CaptionRecord] = []
    for event in word_events:
        if event.get("type") != "WordBoundary":
            continue
        start_ms = int(event.get("offset", 0) / 10_000)
        duration_ms = int(event.get("duration", 100_000) / 10_000)
        end_ms = start_ms + duration_ms
        text = event.get("text", "").strip()
        if text:
            captions.append(
                CaptionRecord(
                    text=text,
                    startMs=start_ms,
                    endMs=end_ms,
                    timestampMs=start_ms,
                    confidence=1.0,
                )
            )
    captions.sort(key=lambda c: c["startMs"])
    return captions


def build_captions_from_narration(
    narration: str,
    duration_ms: int,
) -> list[CaptionRecord]:
    """Fallback: distribute words evenly across the narration duration.

    Used when word-boundary events are unavailable.
    Warning: timestamps are approximate — prefer build_captions_from_word_events.

    Args:
        narration:   The full narration text (all scenes concatenated).
        duration_ms: Total narration duration in milliseconds.

    Returns:
        List of CaptionRecord dicts.
    """
    words = narration.strip().split()
    if not words:
        return []
    ms_per_word = duration_ms / len(words)
    captions: list[CaptionRecord] = []
    for i, word in enumerate(words):
        start_ms = int(i * ms_per_word)
        end_ms = int((i + 1) * ms_per_word)
        captions.append(
            CaptionRecord(
                text=word,
                startMs=start_ms,
                endMs=end_ms,
                timestampMs=start_ms,
                confidence=0.5,  # approximate
            )
        )
    return captions


def validate_captions(
    captions: list[CaptionRecord],
    total_duration_ms: int,
) -> None:
    """Raise ValueError if captions are empty or exceed the video duration.

    Args:
        captions:          List of caption records.
        total_duration_ms: Video duration in ms (should be 30 000).

    Raises:
        ValueError: On validation failure.
    """
    if not captions:
        raise ValueError("Caption list is empty.")
    last_end = max(c["endMs"] for c in captions)
    if last_end > total_duration_ms + 500:  # 500 ms tolerance
        raise ValueError(
            f"Last caption ends at {last_end} ms, which exceeds "
            f"video duration {total_duration_ms} ms."
        )


def save_captions(captions: list[CaptionRecord], path: Path) -> None:
    """Serialise caption list to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(captions, indent=2, ensure_ascii=False), encoding="utf-8")


def load_captions(path: Path) -> list[CaptionRecord]:
    """Load caption list from a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))
