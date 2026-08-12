import subprocess
from pathlib import Path

from src.utility.save_response import SaveLlmResponse
from src.youtube.video_uploader import upload_video


# ============================================================
# STITCH EXISTING VIDEO SCENES ONLY
# NO KIE
# NO VEO
# NO VIDEO GENERATION
# ============================================================

print("=" * 60)
print("STITCHED VIDEO PIPELINE")
print("=" * 60)

# Read the latest generated script metadata
read_data = SaveLlmResponse()
script_id, video_script = read_data.read_response_with_id()

print(f"Script ID: {script_id}")
print(f"Title: {video_script.get('title', 'N/A')}")


# Project paths
project_root = Path(__file__).resolve().parent

scene_dir = project_root / "data" / "metadata" / "scene"

output_dir = (
    project_root
    / "data"
    / script_id
)

output_dir.mkdir(parents=True, exist_ok=True)

concat_file = output_dir / "concat_list.txt"
final_video = output_dir / "video.mp4"


# ============================================================
# FIND EXISTING SCENE VIDEOS
# ============================================================

scene_files = sorted(
    scene_dir.glob("scene_*.mp4"),
    key=lambda p: int(p.stem.split("_")[1])
)

if not scene_files:
    print("\nERROR: No scene MP4 files found.")
    print(f"Expected files inside: {scene_dir}")
    exit(1)

print(f"\nFound {len(scene_files)} scene videos:")

for scene in scene_files:
    print(f"  - {scene.name}")


# ============================================================
# CREATE FFMPEG CONCAT LIST
# ============================================================

with open(concat_file, "w", encoding="utf-8") as f:
    for scene in scene_files:
        # FFmpeg concat format requires forward slashes
        path = scene.resolve().as_posix()

        # Escape single quotes if ever present
        path = path.replace("'", r"'\''")

        f.write(f"file '{path}'\n")

print(f"\nConcat list created:")
print(f"  {concat_file}")


# ============================================================
# STITCH USING FFMPEG
# ============================================================

print("\nStitching videos with FFmpeg...")
print("Please wait...\n")


command = [
    "ffmpeg",
    "-y",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    str(concat_file),
    "-c",
    "copy",
    str(final_video),
]

result = subprocess.run(
    command,
    capture_output=True,
    text=True,
)


# ============================================================
# FALLBACK: RE-ENCODE IF STREAM COPY FAILS
# ============================================================

if result.returncode != 0:

    print("Direct stitching failed.")
    print("Retrying with H.264/AAC re-encoding...\n")

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(final_video),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )


# ============================================================
# CHECK RESULT
# ============================================================

if result.returncode != 0:

    print("\nERROR: FFmpeg failed.")
    print(result.stderr)

    exit(1)


print("\n" + "=" * 60)
print("VIDEO STITCHING SUCCESSFUL")
print("=" * 60)

print(f"\nFinal video:")
print(f"  {final_video.resolve()}")

print(f"\nSize:")
print(f"  {final_video.stat().st_size:,} bytes")


# ============================================================
# PREPARE YOUTUBE METADATA
# ============================================================

narrations = [
    scene.get("narration", "")
    for scene in video_script.get("scenes", [])
    if scene.get("narration")
]

description = (
    f"{video_script.get('title', 'AI Generated Video')}\n\n"
    + "\n".join(narrations)
    + "\n\n#AI #Shorts #Automation"
)

tags = [
    "AI",
    "YouTube Agent",
    "Automation",
    "Shorts",
]

for scene in video_script.get("scenes", []):

    on_screen = scene.get("on_screen_text", "")

    if on_screen:
        tags.append(on_screen.strip())


# ============================================================
# YOUTUBE UPLOAD
# ============================================================

print("\n" + "=" * 60)
print("READY FOR YOUTUBE UPLOAD")
print("=" * 60)

upload_video(
    video_path=final_video,
    title=video_script.get(
        "title",
        "AI Generated Video"
    ),
    description=description,
    tags=tags,
    privacy_status="public",
)