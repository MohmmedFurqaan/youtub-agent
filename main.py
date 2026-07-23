
# importing all the module 
from dotenv import load_dotenv

from model.service.prompt_agent import PromptAgent




user_prompt = str(input("Describ about your video : "))
ai_prompt_agent = PromptAgent(user_prompt)
title = ai_prompt_agent.ai_title_prompt()
print(f"title generated : {title}")