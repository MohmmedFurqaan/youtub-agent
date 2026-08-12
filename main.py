# importing all the modules
from src.model.service.prompt_agent import VideoAgent
from src.model.service.asset_generator import AssetGenerator
from src.utility.load_envs import load_all_env
from src.utility.save_response import SaveLlmResponse
from src.youtube.video_uploader import upload_video

# initialize the devmode
DEVMODE = load_all_env()[1]

# open router initializer
OPENROUTER_MODEL_NAME = load_all_env()[2]

# Phase 1: Generate structured JSON video script
ai_prompt_agent = VideoAgent(
    prompt_from_user="the video on the API rate limiting",
    DEVMODE=DEVMODE,
    open_router_model_name=OPENROUTER_MODEL_NAME,
)

print("Phase 1 — Generating video script …")
video_script = ai_prompt_agent.video_script_generator()


if not DEVMODE:
    # Phase 2: Generate physical assets (images + TTS)
    print("\nPhase 2 — Generating assets …")
    asset_gen = AssetGenerator(script=video_script)
    props_path = asset_gen.generate_assets()

    print(f"\nAll assets generated successfully.")
    print(f"  video-props.json → {props_path}")
else:
    print("skipping the remotion video...")

video_file = SaveLlmResponse.resolve_video_path(filename="video.mp4", directory="data")
if video_file.exists():
    print(f"\nPhase 3 — Uploading video from data folder: {video_file}")
    upload_video(video_file)
else:
    print(f"\nNo video found in data folder to upload: {video_file}")