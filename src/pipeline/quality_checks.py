"""
src/pipeline/quality_checks.py

Validates a generated AI MP4 video before it is permitted to upload.
Uses ffprobe (if available) to read video metadata.

A run is uploadable when:
  ✓ File final.mp4 exists and is non-empty
  ✓ Container: MP4 or MOV
  ✓ Duration: ~30 seconds (25 – 35 seconds window)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from src.utility.file_manipuator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()


def _get_ffprobe_bin() -> str:
    path = shutil.which("ffprobe")
    if path:
        return path
    try:
        import imageio_ffmpeg
        exe_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffprobe_cand = exe_path.parent / "ffprobe.exe"
        if ffprobe_cand.exists():
            return str(ffprobe_cand)
    except Exception:
        pass
    return "ffprobe"


class QualityCheckError(Exception):
    """Raised when one or more quality checks fail."""


class QualityChecker:
    """Runs quality checks on a generated video run."""

    MIN_DURATION_S = 25.0
    MAX_DURATION_S = 35.0

    def __init__(self, mp4_path: Path, run_dir: Path) -> None:
        self.mp4_path = mp4_path
        self.run_dir = run_dir
        self.errors: list[str] = []

    def check_all(self) -> None:
        """Run all checks. Raises QualityCheckError listing every failure."""
        self._check_file_exists()
        probe = self._run_ffprobe()
        if probe:
            self._check_container(probe)
            self._check_duration(probe)

        if self.errors:
            msg = "\n".join(f"  • {e}" for e in self.errors)
            raise QualityCheckError(f"Quality checks failed:\n{msg}")

        logger.info("[quality] All checks passed ✓")

    def _check_file_exists(self) -> None:
        if not FileManipulator.file_exists(self.mp4_path) or self.mp4_path.stat().st_size == 0:
            self.errors.append(f"Output video missing or empty: {self.mp4_path}")

    def _run_ffprobe(self) -> dict | None:
        """Run ffprobe and return parsed JSON output."""
        ffprobe_bin = _get_ffprobe_bin()
        try:
            result = subprocess.run(
                [
                    ffprobe_bin,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    str(self.mp4_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
            logger.warning("[quality] ffprobe check skipped (ffprobe unavailable or error)")
            return None

    def _check_container(self, probe: dict) -> None:
        fmt = probe.get("format", {}).get("format_name", "")
        if "mp4" not in fmt and "mov" not in fmt:
            self.errors.append(f"Expected MP4 container, got: {fmt!r}")

    def _check_duration(self, probe: dict) -> None:
        try:
            duration = float(probe["format"]["duration"])
        except (KeyError, ValueError, TypeError):
            logger.warning("[quality] Could not read duration from ffprobe output.")
            return
        if not (self.MIN_DURATION_S <= duration <= self.MAX_DURATION_S):
            self.errors.append(
                f"Duration {duration:.2f} s is outside the "
                f"{self.MIN_DURATION_S}–{self.MAX_DURATION_S} s window."
            )


# ── Standalone check helper (used from upload command) ────────────────────────


def assert_run_ready_to_upload(run_dir: Path) -> None:
    """Check that a run's final.mp4 passes quality gates before upload."""
    mp4_path = run_dir / "final.mp4"
    if not FileManipulator.exists(mp4_path):
        raise FileNotFoundError(
            f"final.mp4 not found in {run_dir}. Did the video generation complete?"
        )

    run_json_path = run_dir / "run.json"
    if FileManipulator.exists(run_json_path):
        run_data = FileManipulator.read_json(run_json_path, default={})
        if run_data.get("status") != "ready_to_upload":
            raise QualityCheckError(
                f"Run status is {run_data.get('status')!r}, not 'ready_to_upload'. "
                "Fix errors before uploading."
            )

    QualityChecker(mp4_path, run_dir).check_all()
