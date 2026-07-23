
# importing all the module 
from dotenv import load_dotenv
import os 
from pathlib import Path
from model.service.prompt_agent import ai_video_prompt


SYSTEM_VIDEO_PROMPT = Path(
    "prompts/script_video_prompt.md"
).read_text(encoding='utf-8')

user_prompt = str(input("Descrie about your video : "))
response = ai_video_prompt(user_prompt, SYSTEM_VIDEO_PROMPT=SYSTEM_VIDEO_PROMPT)
print(response, flush=True)