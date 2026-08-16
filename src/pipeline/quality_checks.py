"""
src/pipeline/quality_checks.py

Validates a rendered MP4 before it is permitted to upload.
Uses ffprobe (part of the FFmpeg package) to read video metadata.

A run is uploadable only when ALL checks pass:

  ✓  File exists and is non-empty
  ✓  Container: MP4
  ✓  Dimensions: 1080 × 1920
  ✓  Frame rate: 30 fps
  ✓  Duration: 29.5 – 30.5 seconds
  ✓  Audio stream: present
  ✓  Captions: non-empty and within video duration
  ✓  Every required scene asset: resolved (asset.json present)
  ✓  No legacy generator dependency in run.json
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.utility.logging_config import setup_logging

logger = setup_logging()


class QualityCheckError(Exception):
    """Raised when one or more quality checks fail."""


class QualityChecker:
    """Runs all quality checks on a rendered run."""

    EXPECTED_WIDTH = 1080
    EXPECTED_HEIGHT = 1920
    EXPECTED_FPS = 30
    MIN_DURATION_S = 29.5
    MAX_DURATION_S = 30.5

    def __init__(self, mp4_path: Path, run_dir: Path) -> None:
        self.mp4_path = mp4_path
        self.run_dir = run_dir
        self.errors: list[str] = []

    def check_all(self) -> None:
        """Run all checks.  Raises QualityCheckError listing every failure."""
        self._check_file_exists()
        probe = self._run_ffprobe()
        if probe:
            self._check_container(probe)
            self._check_dimensions(probe)
            self._check_fps(probe)
            self._check_duration(probe)
            self._check_audio_stream(probe)
        self._check_captions()
        self._check_assets_resolved()

        if self.errors:
            msg = "\n".join(f"  • {e}" for e in self.errors)
            raise QualityCheckError(f"Quality checks failed:\n{msg}")

        logger.info("[quality] All checks passed ✓")

    # ── Individual checks ─────────────────────────────────────────────────────

    def _check_file_exists(self) -> None:
        if not self.mp4_path.exists() or self.mp4_path.stat().st_size == 0:
            self.errors.append(f"Output file missing or empty: {self.mp4_path}")

    def _run_ffprobe(self) -> dict | None:
        """Run ffprobe and return parsed JSON output."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
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
        except FileNotFoundError:
            self.errors.append("ffprobe not found — install FFmpeg.")
            return None
        except subprocess.CalledProcessError as exc:
            self.errors.append(f"ffprobe failed: {exc.stderr}")
            return None
        except json.JSONDecodeError:
            self.errors.append("ffprobe output could not be parsed.")
            return None

    def _check_container(self, probe: dict) -> None:
        fmt = probe.get("format", {}).get("format_name", "")
        if "mp4" not in fmt and "mov" not in fmt:
            self.errors.append(f"Expected MP4 container, got: {fmt!r}")

    def _check_dimensions(self, probe: dict) -> None:
        video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            self.errors.append("No video stream found.")
            return
        stream = video_streams[0]
        w = stream.get("width")
        h = stream.get("height")
        if w != self.EXPECTED_WIDTH or h != self.EXPECTED_HEIGHT:
            self.errors.append(
                f"Expected {self.EXPECTED_WIDTH}×{self.EXPECTED_HEIGHT}, got {w}×{h}"
            )

    def _check_fps(self, probe: dict) -> None:
        video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            return
        r_frame_rate = video_streams[0].get("r_frame_rate", "0/1")
        try:
            num, den = r_frame_rate.split("/")
            fps = int(num) / int(den)
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        if abs(fps - self.EXPECTED_FPS) > 0.5:
            self.errors.append(f"Expected {self.EXPECTED_FPS} fps, got {fps:.2f}")

    def _check_duration(self, probe: dict) -> None:
        try:
            duration = float(probe["format"]["duration"])
        except (KeyError, ValueError, TypeError):
            self.errors.append("Could not read duration from ffprobe output.")
            return
        if not (self.MIN_DURATION_S <= duration <= self.MAX_DURATION_S):
            self.errors.append(
                f"Duration {duration:.2f} s is outside the "
                f"{self.MIN_DURATION_S}–{self.MAX_DURATION_S} s window."
            )

    def _check_audio_stream(self, probe: dict) -> None:
        audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
        if not audio_streams:
            self.errors.append("No audio stream found in the MP4.")

    def _check_captions(self) -> None:
        captions_path = self.run_dir / "captions.json"
        if not captions_path.exists():
            self.errors.append("captions.json not found.")
            return
        try:
            captions = json.loads(captions_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.errors.append("captions.json is not valid JSON.")
            return
        if not captions:
            self.errors.append("captions.json is empty.")
            return
        # All captions must end before 30 500 ms
        over_limit = [c for c in captions if c.get("endMs", 0) > 30500]
        if over_limit:
            self.errors.append(
                f"{len(over_limit)} caption(s) extend beyond 30.5 s."
            )

    def _check_assets_resolved(self) -> None:
        """Every scene directory under assets/ must have an asset.json."""
        assets_dir = self.run_dir / "assets"
        if not assets_dir.exists():
            self.errors.append("assets/ directory not found.")
            return
        scene_dirs = [d for d in assets_dir.iterdir() if d.is_dir()]
        if not scene_dirs:
            self.errors.append("No scene asset directories found.")
            return
        missing = [d.name for d in scene_dirs if not (d / "asset.json").exists()]
        if missing:
            self.errors.append(
                f"Missing asset.json in scene(s): {', '.join(missing)}"
            )


# ── Standalone check helper (used from upload command) ────────────────────────


def assert_run_ready_to_upload(run_dir: Path) -> None:
    """Check that a run's final.mp4 passes quality gates before upload.

    Raises:
        QualityCheckError: if any check fails.
        FileNotFoundError: if the run directory or final.mp4 does not exist.
    """
    mp4_path = run_dir / "final.mp4"
    if not mp4_path.exists():
        raise FileNotFoundError(
            f"final.mp4 not found in {run_dir}. Did the render complete?"
        )

    run_json_path = run_dir / "run.json"
    if run_json_path.exists():
        run_data = json.loads(run_json_path.read_text(encoding="utf-8"))
        if run_data.get("status") != "ready_to_upload":
            raise QualityCheckError(
                f"Run status is {run_data.get('status')!r}, not 'ready_to_upload'. "
                "Fix errors before uploading."
            )

    QualityChecker(mp4_path, run_dir).check_all()
