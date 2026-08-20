"""
src/media/tts_generator.py

Generates TTS voiceover audio and formatted SRT subtitles from narration text using edge-tts.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import edge_tts

from src.utility.file_manipulator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()


class TTSGenerator:
    """TTS voiceover and subtitle generator using edge-tts."""

    DEFAULT_VOICE = "en-GB-MaisieNeural"

    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        self.voice = voice

    def generate_narration(self, text: str, output_path: Path) -> Path:
        """Generate audio file (mp3) from text.

        Args:
            text: Voice script narration string.
            output_path: Path where narration.mp3 will be saved.

        Returns:
            Path to generated audio file.
        """
        audio_path, _ = self.generate_narration_and_subtitles(text, output_path, None)
        return audio_path

    def generate_narration_and_subtitles(
        self, text: str, output_audio_path: Path, output_srt_path: Path | None = None
    ) -> tuple[Path, Path | None]:
        """Generate audio file (mp3) and optional SRT subtitles from text.

        Args:
            text: Voice script narration string.
            output_audio_path: Path where narration.mp3 will be saved.
            output_srt_path: Optional path where captions.srt will be saved.

        Returns:
            Tuple of (audio_path, srt_path or None).
        """
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Narration text for TTS cannot be empty.")

        FileManipulator.ensure_dir(output_audio_path.parent)
        if output_srt_path:
            FileManipulator.ensure_dir(output_srt_path.parent)

        logger.info("[tts] Synthesizing voiceover and subtitles (voice=%s) …", self.voice)
        asyncio.run(self._synthesize_with_subtitles(cleaned_text, output_audio_path, output_srt_path))
        logger.info("[tts] Voiceover audio generated → %s", output_audio_path)

        return output_audio_path, output_srt_path

    async def _synthesize(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(str(output_path))

    async def _synthesize_with_subtitles(
        self, text: str, output_audio_path: Path, output_srt_path: Path | None
    ) -> None:
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        submaker = edge_tts.SubMaker() if output_srt_path else None

        with open(output_audio_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary") and submaker:
                    submaker.feed(chunk)

        if output_srt_path and submaker:
            raw_srt = submaker.get_srt()
            chunked_srt = _chunk_srt_subtitles(raw_srt, max_words=4)
            FileManipulator.write_text(output_srt_path, chunked_srt)
            logger.info("[tts] SRT Subtitles generated & chunked → %s", output_srt_path)


def _chunk_srt_subtitles(srt_text: str, max_words: int = 4) -> str:
    """Split long sentence SRT entries into short 3–4 word subtitle lines."""
    entries = []
    blocks = srt_text.strip().split("\n\n")
    idx = 1

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        timing = lines[1]
        text = " ".join(lines[2:]).strip()

        match = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", timing)
        if not match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
        t_start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        t_end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        duration = t_end - t_start

        words = text.split()
        if not words:
            continue

        chunks = [words[i : i + max_words] for i in range(0, len(words), max_words)]
        time_per_chunk = duration / len(chunks)

        for i, chunk in enumerate(chunks):
            sub_start = t_start + i * time_per_chunk
            sub_end = t_start + (i + 1) * time_per_chunk

            def fmt_time(t: float) -> str:
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int(round((t - int(t)) * 1000))
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            chunk_text = " ".join(chunk)
            entries.append(f"{idx}\n{fmt_time(sub_start)} --> {fmt_time(sub_end)}\n{chunk_text}")
            idx += 1

    return "\n\n".join(entries)
