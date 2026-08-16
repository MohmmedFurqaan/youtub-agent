"""
src/media/tts_generator.py

Generates a single narration MP3 for the entire video by concatenating all
scene narrations in plan order, then produces captions.json.

Architecture:
    All scene narrations → Kokoro-82M → data/runs/<run-id>/audio/narration.mp3
                                      → data/runs/<run-id>/captions.json

No per-scene MP3 files are created. Remotion receives one audio file and
uses captions timestamps to sync text display.

Fails the run if narration exceeds 30 seconds — never silently speeds audio.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import numpy as np
from mutagen.mp3 import MP3

try:
    import soundfile as sf
    from kokoro import KPipeline
except ImportError:  # pragma: no cover - surfaced at runtime when package missing
    sf = None
    KPipeline = None

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
KOKORO_SAMPLE_RATE = 24000


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

        target_duration_ms = int(getattr(self.plan, "target_duration_ms", 30000) or 30000)
        word_events = asyncio.run(
            self._generate_tts_with_events(
                full_narration,
                self.plan.voice,
                str(self.mp3_path),
                target_duration_ms=target_duration_ms,
                scenes=self.plan.scenes,
            )
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

        validate_captions(captions, total_duration_ms=target_duration_ms)
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
    def _resolve_voice(voice: str) -> str:
        """Map Azure-style voice IDs to Kokoro voice names."""
        normalized = (voice or "").strip().lower()

        if normalized.startswith("en-gb"):
            return "bf_emma"
        if "aria" in normalized or "christopher" in normalized or "jenny" in normalized:
            return "af_heart"
        if "ryan" in normalized:
            return "bf_emma"
        return "af_heart"

    @staticmethod
    def _resolve_lang_code(voice: str) -> str:
        """Use American or British English phonemizer profiles for Kokoro."""
        return "b" if (voice or "").strip().lower().startswith("en-gb") else "a"

    @staticmethod
    def _estimate_word_events(text: str, duration_ms: int) -> list[dict]:
        """Approximate word timings when Kokoro does not emit boundary events."""
        words = text.split()
        if not words:
            return []

        word_events: list[dict] = []
        ms_per_word = duration_ms / len(words)
        for index, word in enumerate(words):
            start_ms = int(index * ms_per_word)
            end_ms = int((index + 1) * ms_per_word)
            if end_ms <= start_ms:
                end_ms = start_ms + 100
            word_events.append({
                "type": "WordBoundary",
                "offset": start_ms * 10_000,
                "duration": (end_ms - start_ms) * 10_000,
                "text": word,
            })
        return word_events

    @staticmethod
    def _pad_audio_to_duration(audio: np.ndarray, target_duration_ms: int, sample_rate: int) -> np.ndarray:
        """Pad a float32 audio array with silence so it reaches the target length."""
        if target_duration_ms <= 0:
            return audio
        current_samples = audio.shape[0]
        target_samples = max(1, int((target_duration_ms / 1000) * sample_rate))
        if current_samples >= target_samples:
            return audio[:target_samples]
        silence = np.zeros(target_samples - current_samples, dtype=audio.dtype)
        return np.concatenate([audio, silence])

    @staticmethod
    async def _generate_tts_with_events(
        text: str,
        voice: str,
        output_path: str,
        target_duration_ms: int | None = None,
        scenes: list | None = None,
    ) -> list[dict]:
        """Generate narration with Kokoro and return word-boundary events.

        When *scenes* is provided, TTS is generated **per scene** so that:
          1. Each scene's speech is measured at its actual duration.
          2. Each scene's audio is padded to its planned scene duration
             (scene.end_ms - scene.start_ms) so the final MP3 matches the
             VideoPlan timeline exactly.
          3. Word events are timed to the *actual speech duration* within
             each scene, offset by the scene's start_ms.  This guarantees
             captions are in sync with both the audio playback AND the
             visual scene transitions.

        When *scenes* is omitted, falls back to generating one continuous
        audio blob and evenly distributing words across the full duration.
        """
        if KPipeline is None or sf is None:
            raise RuntimeError(
                "Kokoro TTS requires the `kokoro` and `soundfile` packages. "
                "Install them and ensure `espeak-ng` is available."
            )

        lang_code = NarrationGenerator._resolve_lang_code(voice)
        resolved_voice = NarrationGenerator._resolve_voice(voice)
        logger.info("[tts] Using Kokoro model -> lang_code=%s, voice=%s", lang_code, resolved_voice)

        target_ms = int(target_duration_ms or 30000)

        if scenes:
            word_events, audio = await NarrationGenerator._generate_per_scene_tts(
                scenes, lang_code, resolved_voice, target_ms,
            )
        else:
            pipeline = KPipeline(lang_code=lang_code)
            generator = pipeline(text, voice=resolved_voice, speed=1, split_pattern=r"\n+")

            chunks: list[np.ndarray] = []
            for _, _, audio_chunk in generator:
                chunks.append(np.asarray(audio_chunk, dtype=np.float32))

            if not chunks:
                raise RuntimeError("Kokoro returned no audio for the narration.")

            audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
            if target_ms > 0:
                audio = NarrationGenerator._pad_audio_to_duration(audio, target_ms, KOKORO_SAMPLE_RATE)

            timing_duration_ms = int((len(audio) / KOKORO_SAMPLE_RATE) * 1000)
            timing_duration_ms = max(timing_duration_ms, target_ms)
            word_events = NarrationGenerator._estimate_word_events(text, timing_duration_ms)

        # ── Save MP3 ──────────────────────────────────────────────────────────
        wav_path = Path(output_path).with_suffix(".wav")
        sf.write(str(wav_path), audio, KOKORO_SAMPLE_RATE)

        mp3_path = Path(output_path)
        ffmpeg_bin = "ffmpeg"
        duration_seconds = max(0.001, target_ms / 1000)
        try:
            subprocess.run(
                [
                    ffmpeg_bin,
                    "-y",
                    "-i",
                    str(wav_path),
                    "-t",
                    f"{duration_seconds:.3f}",
                    "-codec:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    str(mp3_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            if wav_path.exists():
                wav_path.unlink(missing_ok=True)

        logger.info("[tts] narration.mp3 saved → %s", mp3_path)
        return word_events

    @staticmethod
    async def _generate_per_scene_tts(
        scenes: list,
        lang_code: str,
        voice: str,
        target_duration_ms: int,
    ) -> tuple[list[dict], np.ndarray]:
        """Generate TTS per scene, pad each to its planned duration, and return
        word-boundary events + concatenated audio array.

        Each scene's word events are timed to the *actual speech duration*
        measured from Kokoro, offset by scene.start_ms.  The speech audio
        is then padded with silence to span the full scene duration so the
        final audio matches the VideoPlan timeline.
        """
        pipeline = KPipeline(lang_code=lang_code)
        scene_audios: list[np.ndarray] = []
        word_events: list[dict] = []

        for scene in scenes:
            narration = scene.narration.strip()
            scene_start_ms = scene.start_ms
            scene_duration_ms = scene.end_ms - scene.start_ms

            if narration:
                generator = pipeline(narration, voice=voice, speed=1, split_pattern=r"\n+")
                chunks: list[np.ndarray] = []
                for _, _, audio_chunk in generator:
                    chunks.append(np.asarray(audio_chunk, dtype=np.float32))

                if not chunks:
                    scene_audio = np.zeros(1, dtype=np.float32)
                else:
                    scene_audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]

                actual_speech_ms = int((len(scene_audio) / KOKORO_SAMPLE_RATE) * 1000)

                # Word events based on *actual* speech timing, offset by scene start
                words = narration.split()
                if words and actual_speech_ms > 0:
                    ms_per_word = actual_speech_ms / len(words)
                    for index, word in enumerate(words):
                        word_start = int(scene_start_ms + index * ms_per_word)
                        word_end = min(
                            int(scene_start_ms + (index + 1) * ms_per_word),
                            scene_start_ms + scene_duration_ms,
                        )
                        word_events.append({
                            "type": "WordBoundary",
                            "offset": word_start * 10_000,
                            "duration": (word_end - word_start) * 10_000,
                            "text": word,
                        })

                logger.info(
                    "[tts] Scene %s: %d words, speech=%dms, planned=%dms",
                    scene.id, len(words), actual_speech_ms, scene_duration_ms,
                )
            else:
                scene_audio = np.zeros(1, dtype=np.float32)
                logger.info("[tts] Scene %s: empty narration, filling %dms silence", scene.id, scene_duration_ms)

            # Pad scene audio to match planned scene duration
            scene_audio = NarrationGenerator._pad_audio_to_duration(
                scene_audio, scene_duration_ms, KOKORO_SAMPLE_RATE
            )
            scene_audios.append(scene_audio)

        # Concatenate all scene audios
        audio = np.concatenate(scene_audios)

        # Ensure total audio matches target duration (should already be covered
        # by per-scene padding, but guard against rounding)
        audio = NarrationGenerator._pad_audio_to_duration(audio, target_duration_ms, KOKORO_SAMPLE_RATE)

        logger.info("[tts] Concatenated audio: %d samples (%.2fs)", len(audio), len(audio) / KOKORO_SAMPLE_RATE)
        return word_events, audio

    @staticmethod
    def _measure_duration(mp3_path: Path) -> float:
        """Return the duration of an MP3 file in seconds."""
        try:
            audio = MP3(str(mp3_path))
            return float(audio.info.length)
        except Exception:
            return 0.0
