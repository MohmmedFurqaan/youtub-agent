# importing all the module 
from model.service.prompt_agent import VideoAgent
from model.utility.save_response import SaveLlmResponse


ai_prompt_agent = VideoAgent(prompt_from_user="The video on the McP server and why they are usefull", DEVMODE=False)

# logic to generate the video prompt and the title from the model 
video_script = ai_prompt_agent.video_script_generator()
title = ai_prompt_agent.ai_title_prompt(video_script=video_script)
print(video_script)
print(title)

