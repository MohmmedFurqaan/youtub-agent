from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.media.ffmpeg_compositor import FFmpegCompositor
from src.media.tts_generator import TTSGenerator


def test_tts_generator_empty_text(tmp_path):
    generator = TTSGenerator()
    with pytest.raises(ValueError, match="cannot be empty"):
        generator.generate_narration("  ", tmp_path / "out.mp3")


@patch.object(TTSGenerator, "_synthesize_with_subtitles")
def test_tts_generator_success(mock_synth, tmp_path):
    output_mp3 = tmp_path / "audio" / "narration.mp3"
    generator = TTSGenerator()

    async def dummy_synth(text, output_audio_path, output_srt_path):
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        output_mp3.write_bytes(b"dummy mp3 data")

    mock_synth.side_effect = dummy_synth

    result = generator.generate_narration("This is a test script.", output_mp3)

    assert result == output_mp3
    assert result.exists()


@patch("src.media.ffmpeg_compositor.subprocess.run")
def test_ffmpeg_compositor_merge(mock_sub_run, tmp_path):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_sub_run.return_value = mock_res

    video_file = tmp_path / "raw.mp4"
    audio_file = tmp_path / "narration.mp3"
    out_file = tmp_path / "final.mp4"

    video_file.write_bytes(b"video data")
    audio_file.write_bytes(b"audio data")

    def mock_merge(*args, **kwargs):
        out_file.write_bytes(b"merged data")
        return mock_res

    mock_sub_run.side_effect = mock_merge

    merged = FFmpegCompositor.merge_video_and_audio(video_file, audio_file, out_file)
    assert merged == out_file
    assert merged.exists()
    mock_sub_run.assert_called_once()
