"""
YouTube Agent — Main Entry Point

Pipeline:
    Phase 1: Generate structured JSON video script via OpenRouter LLM
    Phase 2: Generate a 30-second video via Seedance 2.5 API
    Phase 3: Upload the video to YouTube with metadata from the script
"""

from pathlib import Path

from src.utility.load_envs import load_all_env
from src.utility.save_response import SaveLlmResponse
from src.model.service.prompt_agent import VideoScriptGeneratorAgent
from src.model.service.video_generator import SeedanceVideoGenerator
from src.youtube.video_uploader import upload_video




OPENROUTER_API_KEY, DEVMODE, OPENROUTER_MODEL_NAME, _, KIE_API_KEY = load_all_env()


print("=" * 60)
print("PHASE 1 — Generating video script")
print("=" * 60)

script_agent = VideoScriptGeneratorAgent(
    prompt_from_user="How chat messages app works through the system design concept",
    DEVMODE=DEVMODE,
    open_router_model_name=OPENROUTER_MODEL_NAME,
)

video_script = script_agent.video_script_generator()

# Read the saved script with its UUID
read_data = SaveLlmResponse()
script_id, video_script = read_data.read_response_with_id()

print(f"  Script ID:  {script_id}")
print(f"  Title:      {video_script.get('title', 'N/A')}")
print(f"  Scenes:     {len(video_script.get('scenes', []))}")


print("\n" + "=" * 60)
print("PHASE 2 — Generating 30s video via Seedance 2.5")
print("=" * 60)

generator = SeedanceVideoGenerator(
    script=video_script,
    api_key=KIE_API_KEY,
    script_id=script_id,
    reference_image_urls=video_script.get("reference_image_urls", []),
)

result = generator.generate_video()

if result.get("error"):
    print(f"\nVideo generation failed: {result['error']}")
    exit(1)

video_path = Path(result["video_path"])

print(f"\n  Task ID:    {result['task_id']}")
print(f"  Video:      {video_path}")
print(f"  Size:       {video_path.stat().st_size:,} bytes")



print("\n" + "=" * 60)
print("PHASE 3 — Uploading to YouTube")
print("=" * 60)

youtube_meta = video_script.get("youtube", {})

# Build description from youtube metadata + scene narrations
narrations = [
    scene.get("narration", "")
    for scene in video_script.get("scenes", [])
    if scene.get("narration")
]

description = youtube_meta.get("description", video_script.get("title", "AI Generated Video"))
description += "\n\n" + "\n".join(narrations)
description += "\n\n#AI #Shorts #Automation"

tags = youtube_meta.get("tags", ["AI", "YouTube Agent", "Automation", "Shorts"])

upload_video(
    video_path=video_path,
    title=video_script.get("title", "AI Generated Video"),
    description=description,
    tags=tags,
    category_id=youtube_meta.get("category_id", "22"),
    privacy_status="public",
)

print("\nDone.")