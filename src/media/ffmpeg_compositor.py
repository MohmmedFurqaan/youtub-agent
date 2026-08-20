"""
src/media/ffmpeg_compositor.py

Merges AI video with TTS voiceover audio and optional subtitles using FFmpeg.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.utility.file_manipulator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()


def _get_ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return "ffmpeg"


class FFmpegCompositor:
    """Handles audio/video stream multiplexing and subtitle burning using FFmpeg."""

    @staticmethod
    def merge_video_and_audio(
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        srt_path: Path | None = None,
    ) -> Path:
        """Merge video and audio tracks into output_path, optionally burning SRT captions.

        Args:
            video_path: Input video file (e.g. raw Grok AI video MP4).
            audio_path: Input audio file (e.g. narration.mp3).
            output_path: Target output MP4 path.
            srt_path: Optional path to SRT captions file for burning subtitles.

        Returns:
            Path to the merged final MP4 file.
        """
        if not FileManipulator.file_exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not FileManipulator.file_exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        ffmpeg_bin = _get_ffmpeg_bin()

        if video_path.resolve() == output_path.resolve():
            temp_output = output_path.parent / f"merged_{output_path.name}"
        else:
            temp_output = output_path

        FileManipulator.ensure_dir(temp_output.parent)

        if srt_path and FileManipulator.file_exists(srt_path):
            srt_posix = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")
            sub_filter = (
                f"subtitles=filename='{srt_posix}':force_style="
                "'FontSize=12,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,BorderStyle=1,Outline=1.5,Alignment=2,MarginV=30'"
            )
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", str(video_path.resolve()),
                "-i", str(audio_path.resolve()),
                "-vf", sub_filter,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                str(temp_output.resolve()),
            ]
        else:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", str(video_path.resolve()),
                "-i", str(audio_path.resolve()),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(temp_output.resolve()),
            ]

        logger.info("[ffmpeg] Merging audio/video (burn_subtitles=%s): %s", bool(srt_path), " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error("[ffmpeg] Error merging video/audio: %s", result.stderr)
            raise RuntimeError(f"FFmpeg audio/video merge failed: {result.stderr}")

        if temp_output != output_path:
            FileManipulator.copy_file(temp_output, output_path)
            FileManipulator.delete_file(temp_output)

        logger.info("[ffmpeg] Audio and video merged successfully → %s", output_path)
        return output_path
