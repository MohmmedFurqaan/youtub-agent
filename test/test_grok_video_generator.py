from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.media.grok_video_generator import GrokVideoGenerator


def test_grok_video_generator_init():
    with pytest.raises(ValueError):
        GrokVideoGenerator(kie_api_key="")

    client = GrokVideoGenerator(kie_api_key="  test_key_123  ")
    assert client.api_key == "test_key_123"
    assert client.headers["Authorization"] == "Bearer test_key_123"


@patch("src.media.grok_video_generator.requests.post")
def test_create_task(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 200,
        "msg": "success",
        "data": {"taskId": "task-abc-123"}
    }
    mock_post.return_value = mock_response

    client = GrokVideoGenerator(kie_api_key="test_key")
    task_id = client.create_task(prompt="   A motion prompt  ", duration=30, resolution="480p")

    assert task_id == "task-abc-123"
    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "grok-imagine/text-to-video"
    assert payload["input"]["prompt"] == "A motion prompt"
    assert payload["input"]["duration"] == 30
    assert payload["input"]["resolution"] == "480p"


@patch("src.media.grok_video_generator.requests.get")
def test_poll_task_status_success(mock_get):
    # First response: waiting, Second response: success
    resp_waiting = MagicMock()
    resp_waiting.status_code = 200
    resp_waiting.json.return_value = {
        "code": 200,
        "data": {"taskId": "task-abc", "state": "waiting"}
    }

    resp_success = MagicMock()
    resp_success.status_code = 200
    resp_success.json.return_value = {
        "code": 200,
        "data": {
            "taskId": "task-abc",
            "state": "success",
            "resultJson": '{"resultUrls":["https://example.com/video.mp4"]}'
        }
    }

    mock_get.side_effect = [resp_waiting, resp_success]

    client = GrokVideoGenerator(kie_api_key="test_key")
    video_url = client.poll_task_status("task-abc", poll_interval=0, timeout=10)

    assert video_url == "https://example.com/video.mp4"
    assert mock_get.call_count == 2


@patch.object(GrokVideoGenerator, "download_file")
@patch.object(GrokVideoGenerator, "poll_task_status")
@patch.object(GrokVideoGenerator, "create_task")
def test_generate_video_flow(mock_create, mock_poll, mock_download, tmp_path):
    mock_create.return_value = "task-123"
    mock_poll.return_value = "https://example.com/generated.mp4"

    def mock_dl(url, dest):
        dest.write_bytes(b"dummy mp4 data")
        return dest

    mock_download.side_effect = mock_dl

    client = GrokVideoGenerator(kie_api_key="test_key")
    output = client.generate_video("  Motion prompt text  ", tmp_path)

    assert output == tmp_path / "final.mp4"
    assert output.exists()
    mock_create.assert_called_once()
    mock_poll.assert_called_once_with("task-123", poll_interval=5, timeout=600)
    mock_download.assert_called_once_with("https://example.com/generated.mp4", tmp_path / "final.mp4")
