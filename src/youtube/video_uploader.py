from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.utility.load_envs import load_all_env

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_oauth_config() -> dict:
    _, _, _, youtube_config = load_all_env()
    return youtube_config


def upload_video(video_path: str | Path | None = None, title: str = "Sample AI Generated Reel"):
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
            "description": "Uploaded automatically using the YouTube Data API.",
            "tags": ["AI", "YouTube Agent", "Automation", "Test"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
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
    print("\nVideo ID:")
    print(video_id)
    print("\nYouTube URL:")
    print(f"https://www.youtube.com/watch?v={video_id}")
    print("\nPrivacy:")
    print("PUBLIC")
    print("\n====================================")
    return response

