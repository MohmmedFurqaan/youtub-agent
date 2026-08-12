from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.utility.load_envs import load_all_env

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


import json
from pathlib import Path

def get_youtube_oauth_config() -> dict:
    credentials_path = Path(__file__).resolve().parents[2] / "credentials.json"

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"YouTube OAuth credentials not found: {credentials_path}"
        )

    with open(credentials_path, "r", encoding="utf-8") as f:
        return json.load(f)

def upload_video(
    video_path: str | Path | None = None,
    title: str = "Sample AI Generated Reel",
    description: str = "Uploaded automatically using the YouTube Data API.",
    tags: list[str] | None = None,
    category_id: str = "22",
    privacy_status: str = "public",
):
    '''Upload a video to YouTube with full metadata.

    Args:
        video_path: Path to the video file.
        title: Video title.
        description: Video description.
        tags: List of tags/keywords.
        category_id: YouTube category ID (default 22 = People & Blogs).
        privacy_status: "public", "private", or "unlisted".
    Returns:
        YouTube API response dict.
    '''
    if tags is None:
        tags = ["AI", "YouTube Agent", "Automation"]

    if video_path is None:
        from src.utility.save_response import SaveLlmResponse
        video_path = SaveLlmResponse.resolve_video_path()

    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_file}")

    print(f"Video found: {video_file.resolve()}")
    print("\nStarting Google OAuth...")

    flow = InstalledAppFlow.from_client_config(get_youtube_oauth_config(), SCOPES)
    credentials = flow.run_local_server(port=0)

    youtube = build("youtube", "v3", credentials=credentials)

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

    print("\nUploading video...")
    print("Please wait...\n")

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print("\n====================================")
    print("       UPLOAD SUCCESSFUL!")
    print("====================================")
    print(f"\nVideo ID: {video_id}")
    print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
    print(f"Privacy: {privacy_status.upper()}")
    print("====================================")
    return response
