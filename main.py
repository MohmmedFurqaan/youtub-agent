# importing all the modules
from model.service.prompt_agent import VideoAgent
from model.service.asset_generator import AssetGenerator

# ── Phase 1: Generate structured JSON video script ─────────────────────────
ai_prompt_agent = VideoAgent(
    prompt_from_user="The video on MCP servers and why they are useful",
    DEVMODE=False,
)

print("▶ Phase 1 — Generating video script …")
video_script = ai_prompt_agent.video_script_generator()
print("✔ Script generated:")
print(video_script)

# ── Phase 2: Generate physical assets (images + TTS) ──────────────────────
print("\n▶ Phase 2 — Generating assets …")
asset_gen = AssetGenerator(script=video_script)
props_path = asset_gen.generate_assets()

print(f"\n✔ All assets generated successfully.")
print(f"  video-props.json → {props_path}")
