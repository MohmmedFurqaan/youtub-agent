"""
test/test_quality_checks.py

Unit tests for QualityChecker with Grok Imagine AI Video pipeline.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from src.pipeline.quality_checks import QualityCheckError, QualityChecker


def _good_ffprobe_output() -> dict:
    return {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "30.0",
        },
    }


def test_quality_check_pass(tmp_path):
    run_dir = tmp_path / "runs" / "test-run"
    run_dir.mkdir(parents=True)
    mp4 = run_dir / "final.mp4"
    mp4.write_bytes(b"\x00" * 1024)

    checker = QualityChecker(mp4, run_dir)
    with patch.object(checker, "_run_ffprobe", return_value=_good_ffprobe_output()):
        checker.check_all()

    assert checker.errors == []


def test_quality_check_file_missing(tmp_path):
    run_dir = tmp_path / "runs" / "test-run"
    run_dir.mkdir(parents=True)
    mp4 = run_dir / "final.mp4"

    checker = QualityChecker(mp4, run_dir)
    checker._check_file_exists()
    assert len(checker.errors) == 1
    assert "missing" in checker.errors[0].lower() or "empty" in checker.errors[0].lower()


def test_quality_check_duration_out_of_range(tmp_path):
    run_dir = tmp_path / "runs" / "test-run"
    run_dir.mkdir(parents=True)
    mp4 = run_dir / "final.mp4"
    mp4.write_bytes(b"\x00" * 1024)

    bad_probe = {
        "format": {
            "format_name": "mp4",
            "duration": "10.0",
        }
    }

    checker = QualityChecker(mp4, run_dir)
    with patch.object(checker, "_run_ffprobe", return_value=bad_probe):
        with pytest.raises(QualityCheckError):
            checker.check_all()
