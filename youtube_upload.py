import os

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

VIDEO_FILE = os.path.join(
    "uploads",
    "sample.mp4"
)


# ============================================================
# YOUTUBE UPLOAD
# ============================================================

def upload_video():

    # Check video
    if not os.path.exists(VIDEO_FILE):
        print("ERROR: Video file not found!")
        print("Expected:", os.path.abspath(VIDEO_FILE))
        return

    # Check credentials
    if not os.path.exists("credentials.json"):
        print("ERROR: credentials.json not found!")
        return

    print("Video found:")
    print(os.path.abspath(VIDEO_FILE))

    print("\nStarting Google OAuth...")

    # --------------------------------------------------------
    # Google OAuth
    # --------------------------------------------------------

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    credentials = flow.run_local_server(
        port=0
    )

    # --------------------------------------------------------
    # YouTube API
    # --------------------------------------------------------

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    # --------------------------------------------------------
    # Video information
    # --------------------------------------------------------

    request_body = {
        "snippet": {
            "title": "Sample AI Generated Reel",
            "description": (
                "Test video uploaded automatically "
                "using the YouTube Data API."
            ),
            "tags": [
                "AI",
                "YouTube Agent",
                "Automation",
                "Test"
            ],
            "categoryId": "22"
        },

        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    # --------------------------------------------------------
    # Video file
    # --------------------------------------------------------

    media = MediaFileUpload(
        VIDEO_FILE,
        mimetype="video/mp4",
        chunksize=1024 * 1024,
        resumable=True
    )

    print("\nUploading video...")
    print("Please wait...\n")

    # --------------------------------------------------------
    # Upload request
    # --------------------------------------------------------

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None

    while response is None:

        status, response = request.next_chunk()

        if status:
            progress = int(
                status.progress() * 100
            )

            print(
                f"Upload progress: {progress}%"
            )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    video_id = response["id"]

    print("\n====================================")
    print("       UPLOAD SUCCESSFUL!")
    print("====================================")

    print("\nVideo ID:")
    print(video_id)

    print("\nYouTube URL:")
    print(
        f"https://www.youtube.com/watch?v={video_id}"
    )

    print("\nPrivacy:")
    print("PUBLIC")

    print("\n====================================")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    upload_video()