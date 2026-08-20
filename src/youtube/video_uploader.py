"""
src/youtube/video_uploader.py

Upload a completed run's final.mp4 to YouTube.

Authentication uses environment-based OAuth (InstalledAppFlow.from_client_config)
so no credentials.json file is needed.  Refreshed credentials are stored in
data/youtube_token.json (outside Git).

Default privacy: private.  Use --publish to make a video public.

After upload, writes data/runs/<run-id>/youtube.json with the video ID and
upload timestamp.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.oauth2.credentials

from src.utility.file_manipuator import FileManipulator
from src.utility.logging_config import setup_logging

logger = setup_logging()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

_PROJECT_ROOT = FileManipulator.get_project_root()
_TOKEN_PATH = _PROJECT_ROOT / "data" / "youtube_token.json"


def _get_credentials(youtube_config: dict):
    """Return valid OAuth credentials, refreshing from disk cache when possible."""

    # Try to load saved token
    if FileManipulator.exists(_TOKEN_PATH):
        try:
            info = FileManipulator.read_json(_TOKEN_PATH)
            if info:
                creds = google.oauth2.credentials.Credentials.from_authorized_user_info(
                    info, SCOPES
                )
                if creds and creds.valid:
                    logger.info("[uploader] Using cached OAuth token from %s", _TOKEN_PATH)
                    return creds
        except Exception as exc:
            logger.warning("[uploader] Could not load cached token: %s", exc)

    # Run OAuth flow (opens browser)
    logger.info("[uploader] Starting OAuth flow …")
    flow = InstalledAppFlow.from_client_config(youtube_config, SCOPES)
    creds = flow.run_local_server(port=0)

    # Persist token for future runs
    FileManipulator.write_text(_TOKEN_PATH, creds.to_json())
    logger.info("[uploader] OAuth token saved → %s", _TOKEN_PATH)

    return creds


def upload_video(
    run_id: str,
    run_dir: Path,
    youtube_config: dict,
    privacy_status: str = "private",
) -> dict:
    """Upload a run's final.mp4 to YouTube.

    Reads metadata from plan.json in the run directory.
    Writes youtube.json with the returned video ID and upload timestamp.

    Args:
        run_id:         The run UUID.
        run_dir:        Path to data/runs/<run-id>/.
        youtube_config: OAuth client config dict (from load_all_env).
        privacy_status: "private" (default) or "public".

    Returns:
        The YouTube API response dict.

    Raises:
        FileNotFoundError: If final.mp4 or plan.json is missing.
        ValueError: If privacy_status is not valid.
    """
    if privacy_status not in ("private", "public", "unlisted"):
        raise ValueError(
            f"privacy_status must be 'private', 'public', or 'unlisted'; got {privacy_status!r}"
        )

    video_file = run_dir / "final.mp4"
    plan_file = run_dir / "plan.json"

    if not FileManipulator.exists(video_file):
        raise FileNotFoundError(f"final.mp4 not found: {video_file}")
    if not FileManipulator.exists(plan_file):
        raise FileNotFoundError(f"plan.json not found: {plan_file}")

    # Read metadata from plan.json
    plan_data = FileManipulator.read_json(plan_file, default={})
    yt = plan_data.get("youtube", {})
    title = yt.get("title", "AI Generated Short")
    description = yt.get("description", "")
    tags = yt.get("tags", [])
    category_id = yt.get("category_id", "22")

    # Append scene narrations to description
    narrations = [
        scene.get("narration", "")
        for scene in plan_data.get("scenes", [])
        if scene.get("narration")
    ]
    if narrations:
        description += "\n\n" + " ".join(narrations)
    description += "\n\n#AI #Shorts #Automation"

    print(f"\nUploading run: {run_id}")
    print(f"Title:   {title}")
    print(f"Privacy: {privacy_status.upper()}")
    print("\nStarting Google OAuth…")

    creds = _get_credentials(youtube_config)
    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_file),
        mimetype="video/mp4",
        chunksize=1024 * 1024,
        resumable=True,
    )

    print("\nUploading…")
    # pyrefly: ignore [missing-attribute]
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%")

    video_id = response["id"]

    # Save youtube.json
    youtube_json = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "privacy": privacy_status,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
    }
    youtube_path = run_dir / "youtube.json"
    FileManipulator.write_json(youtube_path, youtube_json, indent=2)

    print("\n" + "=" * 50)
    print("  UPLOAD SUCCESSFUL")
    print("=" * 50)
    print(f"  Video ID: {video_id}")
    print(f"  URL:      https://www.youtube.com/watch?v={video_id}")
    print(f"  Privacy:  {privacy_status.upper()}")
    print(f"  Saved:    {youtube_path}")
    print("=" * 50)

    return response
