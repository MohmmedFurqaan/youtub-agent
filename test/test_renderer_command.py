"""
test/test_renderer_command.py

Verifies that the renderer subprocess command is constructed correctly
and does NOT use shell interpolation.

Run with:  uv run pytest test/test_renderer_command.py -v
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import call, patch, MagicMock
import uuid
# pyrefly: ignore [missing-import]
from src.pipeline.run_pipeline import RunPipeline


import pytest


def _make_pipeline(tmp_path: Path):
    """Create a RunPipeline with run_dir in tmp_path."""

    run_id = str(uuid.uuid4())
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)

    pipeline = object.__new__(RunPipeline)
    pipeline.topic = "test topic"
    pipeline.model_name = "test-model"
    pipeline.cached_plan_path = None
    pipeline.run_id = run_id
    pipeline.run_dir = run_dir
    return pipeline


class TestRendererCommand:
    def test_command_is_a_list(self, tmp_path):
        """subprocess.run must be called with a list, not a shell string."""
        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline.run_dir / "props.json"
        props_path.write_text("{}")
        output_mp4 = pipeline.run_dir / "final.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            pipeline._render(props_path, output_mp4)

            called_args = mock_run.call_args
            # First positional arg must be a list
            cmd = called_args[0][0]
            assert isinstance(cmd, list), "Command must be a list, not a string"

    def test_command_contains_required_parts(self, tmp_path):
        """Command must include npx, remotion, render, ShortVideo, output, and --props."""
        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline.run_dir / "props.json"
        props_path.write_text("{}")
        output_mp4 = pipeline.run_dir / "final.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            pipeline._render(props_path, output_mp4)

            cmd = mock_run.call_args[0][0]
            cmd_str = " ".join(str(c) for c in cmd)

            assert "npx" in cmd or any("remotion" in str(c) for c in cmd)
            assert any("remotion" in str(c) for c in cmd)
            assert "render" in cmd
            assert "ShortVideo" in cmd
            assert any("props.json" in c for c in cmd)
            assert any("final.mp4" in c for c in cmd)

    def test_no_shell_true(self, tmp_path):
        """subprocess.run must NOT be called with shell=True."""
        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline.run_dir / "props.json"
        props_path.write_text("{}")
        output_mp4 = pipeline.run_dir / "final.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            pipeline._render(props_path, output_mp4)

            kwargs = mock_run.call_args[1]
            assert kwargs.get("shell") is not True

    def test_check_true(self, tmp_path):
        """subprocess.run must be called with check=True."""
        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline.run_dir / "props.json"
        props_path.write_text("{}")
        output_mp4 = pipeline.run_dir / "final.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            pipeline._render(props_path, output_mp4)

            kwargs = mock_run.call_args[1]
            assert kwargs.get("check") is True

    def test_cwd_is_renderer_dir(self, tmp_path):
        """subprocess must run inside video-renderer/."""
        # pyrefly: ignore [missing-import]
        from src.pipeline.run_pipeline import _RENDERER_DIR

        pipeline = _make_pipeline(tmp_path)
        props_path = pipeline.run_dir / "props.json"
        props_path.write_text("{}")
        output_mp4 = pipeline.run_dir / "final.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            pipeline._render(props_path, output_mp4)

            kwargs = mock_run.call_args[1]
            assert str(kwargs.get("cwd")) == str(_RENDERER_DIR)
