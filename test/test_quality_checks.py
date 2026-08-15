"""
test/test_quality_checks.py

Unit tests for QualityChecker.  ffprobe is mocked so no real video file
is required.
Run with:  uv run pytest test/test_quality_checks.py -v
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.quality_checks import QualityCheckError, QualityChecker


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _good_ffprobe_output() -> dict:
    """Minimal ffprobe JSON that passes every check."""
    return {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "30.0",
        },
        "streams": [
            {
                "codec_type": "video",
                "width": 1080,
                "height": 1920,
                "r_frame_rate": "30/1",
            },
            {
                "codec_type": "audio",
            },
        ],
    }


def _setup_run_dir(tmp_path: Path, mp4_name: str = "final.mp4") -> tuple[Path, Path]:
    """Create a minimal run directory and a dummy MP4 file."""
    run_dir = tmp_path / "runs" / "test-run-id"
    run_dir.mkdir(parents=True)

    mp4 = run_dir / mp4_name
    mp4.write_bytes(b"\x00" * 1024)  # non-empty file

    # captions.json
    captions = [{"text": "hello", "startMs": 0, "endMs": 500, "timestampMs": 0, "confidence": 1.0}]
    (run_dir / "captions.json").write_text(json.dumps(captions))

    # assets dir with scene dirs
    assets_dir = run_dir / "assets"
    scene_dir = assets_dir / "scene-01"
    scene_dir.mkdir(parents=True)
    (scene_dir / "asset.json").write_text('{"source": "diagram"}')

    return run_dir, mp4


# ── Passing run ───────────────────────────────────────────────────────────────


class TestQualityCheckPass:
    def test_all_checks_pass(self, tmp_path):
        run_dir, mp4 = _setup_run_dir(tmp_path)
        checker = QualityChecker(mp4, run_dir)

        with patch.object(checker, "_run_ffprobe", return_value=_good_ffprobe_output()):
            checker.check_all()  # should not raise

        assert checker.errors == []


# ── Individual failure cases ──────────────────────────────────────────────────


class TestQualityCheckFailures:

    def _run_checker(self, tmp_path, probe_override: dict) -> list[str]:
        run_dir, mp4 = _setup_run_dir(tmp_path)
        checker = QualityChecker(mp4, run_dir)
        with patch.object(checker, "_run_ffprobe", return_value=probe_override):
            try:
                checker.check_all()
            except QualityCheckError:
                pass
        return checker.errors

    def test_wrong_dimensions(self, tmp_path):
        probe = _good_ffprobe_output()
        probe["streams"][0]["width"] = 720
        probe["streams"][0]["height"] = 1280
        errors = self._run_checker(tmp_path, probe)
        assert any("1080" in e for e in errors)

    def test_wrong_fps(self, tmp_path):
        probe = _good_ffprobe_output()
        probe["streams"][0]["r_frame_rate"] = "24/1"
        errors = self._run_checker(tmp_path, probe)
        assert any("fps" in e.lower() or "24" in e for e in errors)

    def test_duration_too_short(self, tmp_path):
        probe = _good_ffprobe_output()
        probe["format"]["duration"] = "28.0"
        errors = self._run_checker(tmp_path, probe)
        assert any("28" in e or "Duration" in e for e in errors)

    def test_duration_too_long(self, tmp_path):
        probe = _good_ffprobe_output()
        probe["format"]["duration"] = "31.5"
        errors = self._run_checker(tmp_path, probe)
        assert any("31" in e or "Duration" in e for e in errors)

    def test_no_audio_stream(self, tmp_path):
        probe = _good_ffprobe_output()
        probe["streams"] = [s for s in probe["streams"] if s["codec_type"] != "audio"]
        errors = self._run_checker(tmp_path, probe)
        assert any("audio" in e.lower() for e in errors)

    def test_file_missing(self, tmp_path):
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        mp4 = run_dir / "final.mp4"  # does not exist
        checker = QualityChecker(mp4, run_dir)
        checker._check_file_exists()
        assert any("missing" in e.lower() or "empty" in e.lower() for e in checker.errors)

    def test_captions_empty(self, tmp_path):
        run_dir, mp4 = _setup_run_dir(tmp_path)
        (run_dir / "captions.json").write_text("[]")
        checker = QualityChecker(mp4, run_dir)
        checker._check_captions()
        assert any("empty" in e.lower() for e in checker.errors)

    def test_captions_over_limit(self, tmp_path):
        run_dir, mp4 = _setup_run_dir(tmp_path)
        captions = [{"text": "late", "startMs": 30000, "endMs": 32000, "timestampMs": 30000, "confidence": 1.0}]
        (run_dir / "captions.json").write_text(json.dumps(captions))
        checker = QualityChecker(mp4, run_dir)
        checker._check_captions()
        assert any("30.5" in e or "beyond" in e.lower() for e in checker.errors)

    def test_missing_asset_json(self, tmp_path):
        run_dir, mp4 = _setup_run_dir(tmp_path)
        # Remove the asset.json from the scene dir
        (run_dir / "assets" / "scene-01" / "asset.json").unlink()
        checker = QualityChecker(mp4, run_dir)
        checker._check_assets_resolved()
        assert any("scene-01" in e for e in checker.errors)
