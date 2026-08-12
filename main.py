# importing all the modules
from src.model.service.prompt_agent import VideoScriptGeneratorAgent
from src.model.service.asset_generator import AssetGenerator
from src.utility.load_envs import load_all_env
from src.utility.save_response import SaveLlmResponse
from src.youtube.video_uploader import upload_video
from src.model.service.video_generator import VideoGeneratorAgent

# load all environment variables
envs = load_all_env()
DEVMODE = envs[1]
OPENROUTER_MODEL_NAME = envs[2]
KIE_API_KEY = envs[4]

# Phase 1: Generate structured JSON video script
ai_prompt_agent = VideoScriptGeneratorAgent(
    prompt_from_user="the video on designing an API rate limiter from scratch",
    DEVMODE=DEVMODE,
    open_router_model_name=OPENROUTER_MODEL_NAME,
)

print("Phase 1 — Generating video script ...")
video_script = ai_prompt_agent.video_script_generator()


if not DEVMODE:
    # Phase 2: Generate physical assets (images + TTS)
    print("\nPhase 2 — Generating assets ...")
    asset_gen = AssetGenerator(script=video_script)
    props_path = asset_gen.generate_assets()

    print(f"\nAll assets generated successfully.")
    print(f"  video-props.json -> {props_path}")
else:
    print("skipping the remotion video...")

# Phase 3: Generate video clips via Veo 3.1 API
print("\n" + "=" * 50)
print("Phase 3 — Generating video via Veo 3.1 API ...")
print("=" * 50)

read_data = SaveLlmResponse()
script_id, video_script = read_data.read_response_with_id()

print(f"  Script ID: {script_id}")
print(f"  Title: {video_script.get('title', 'N/A')}")
print(f"  Scenes: {len(video_script.get('scenes', []))}")

video_generator_agent = VideoGeneratorAgent(
    script=video_script,
    KIE_API_KEY=KIE_API_KEY,
    script_id=script_id,
)

result = video_generator_agent.generate_full_video()

# Check if generation failed
if "error" in result:
    print(f"\nVideo generation failed: {result['error']}")
    exit(1)

print("\nVideo generation complete.")
print(f"  Task chain: {result['task_chain']}")
print(f"  Scene files: {result['scene_files']}")
print(f"  Final video: {result['final_video']}")

# Phase 4: Upload to YouTube
final_video_path = result.get("final_video")
if final_video_path:
    print("\n" + "=" * 50)
    print("Phase 4 — Uploading video to YouTube ...")
    print("=" * 50)

    # Build description from the script narrations
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

    # Extract tags from on_screen_text of each scene
    tags = ["AI", "YouTube Agent", "Automation", "Shorts"]
    for scene in video_script.get("scenes", []):
        on_screen = scene.get("on_screen_text", "")
        if on_screen:
            tags.append(on_screen.strip())

    upload_video(
        video_path=final_video_path,
        title=video_script.get("title", "AI Generated Video"),
        description=description,
        tags=tags,
        privacy_status="public",
    )
else:
    print("\nNo final video was produced. Skipping YouTube upload.")