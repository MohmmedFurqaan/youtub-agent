"""
src/media/tts_generator.py

Generates a single narration MP3 for the entire video by concatenating all
scene narrations in plan order, then produces captions.json.

Architecture:
    All scene narrations → edge-tts → data/runs/<run-id>/audio/narration.mp3
                                   → data/runs/<run-id>/captions.json

No per-scene MP3 files are created.  Remotion receives one audio file and
uses captions timestamps to sync text display.

Fails the run if narration exceeds 30 seconds — never silently speeds audio.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

from src.contracts.video_plan import VideoPlan
from src.media.captions import (
    CaptionRecord,
    build_captions_from_narration,
    build_captions_from_word_events,
    save_captions,
    validate_captions,
)
from src.utility.logging_config import setup_logging

logger = setup_logging()

# Hard limit: narration may not exceed 30.5 s (0.5 s tolerance)
MAX_NARRATION_DURATION_S = 30.5
FPS = 30


class TTSResult:
    """Result of a TTS generation run."""

    def __init__(
        self,
        mp3_path: Path,
        duration_ms: int,
        captions: list[CaptionRecord],
    ) -> None:
        self.mp3_path = mp3_path
        self.duration_ms = duration_ms
        self.captions = captions


class NarrationGenerator:
    """Generates one MP3 + captions.json for the entire VideoPlan."""

    def __init__(self, plan: VideoPlan, run_dir: Path) -> None:
        self.plan = plan
        self.audio_dir = run_dir / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.mp3_path = self.audio_dir / "narration.mp3"
        self.captions_path = run_dir / "captions.json"

    # ── Public ────────────────────────────────────────────────────────────────

    def generate(self) -> TTSResult:
        """Generate narration and captions, enforce the 30-second limit.

        Returns:
            TTSResult with paths and caption data.

        Raises:
            RuntimeError: If narration exceeds MAX_NARRATION_DURATION_S.
        """
        full_narration = self._build_full_narration()
        logger.info("[tts] Full narration (%d chars): %s…", len(full_narration), full_narration[:80])

        word_events = asyncio.run(
            self._generate_tts_with_events(full_narration, self.plan.voice, str(self.mp3_path))
        )
        logger.info("[tts] narration.mp3 saved → %s", self.mp3_path)

        duration_s = self._measure_duration(self.mp3_path)
        duration_ms = int(duration_s * 1000)
        logger.info("[tts] Duration: %.2f s (%d ms)", duration_s, duration_ms)

        if duration_s > MAX_NARRATION_DURATION_S:
            raise RuntimeError(
                f"Narration is {duration_s:.1f} s — exceeds the 30-second limit. "
                "Regenerate the VideoPlan with shorter narrations."
            )

        # Build captions from word-boundary events (preferred) or fallback
        if word_events:
            captions = build_captions_from_word_events(word_events)
            logger.info("[tts] Built %d captions from word-boundary events.", len(captions))
        else:
            logger.warning("[tts] No word-boundary events; falling back to even distribution.")
            captions = build_captions_from_narration(full_narration, duration_ms)

        validate_captions(captions, total_duration_ms=30000)
        save_captions(captions, self.captions_path)
        logger.info("[tts] captions.json saved → %s", self.captions_path)

        return TTSResult(
            mp3_path=self.mp3_path,
            duration_ms=duration_ms,
            captions=captions,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _build_full_narration(self) -> str:
        """Concatenate all scene narrations with a short pause between them."""
        parts = [scene.narration.strip() for scene in self.plan.scenes if scene.narration.strip()]
        return "  ".join(parts)  # double-space → slight TTS pause

    @staticmethod
    async def _generate_tts_with_events(
        text: str,
        voice: str,
        output_path: str,
    ) -> list[dict]:
        """Run edge-tts and collect word-boundary events.

        Returns:
            List of word-boundary event dicts.  May be empty if the provider
            does not emit them (handled by the caller).
        """
        communicate = edge_tts.Communicate(text=text, voice=voice)
        word_events: list[dict] = []

        # Collect word boundary events while saving audio
        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_events.append({
                        "type": "WordBoundary",
                        "offset": chunk.get("offset", 0),
                        "duration": chunk.get("duration", 0),
                        "text": chunk.get("text", ""),
                    })

        return word_events

    @staticmethod
    def _measure_duration(mp3_path: Path) -> float:
        """Return the duration of an MP3 file in seconds."""
        try:
            audio = MP3(str(mp3_path))
            return float(audio.info.length)
        except Exception:
            return 0.0
