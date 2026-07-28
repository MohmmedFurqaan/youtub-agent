# importing all the module 
from model.service.prompt_agent import VideoAgent
from model.utility.save_response import SaveLlmResponse

# do not take the input if the response is saved 

user_input = input("Enter you video description : ")
ai_prompt_agent = VideoAgent(prompt_from_user=user_input)



video = ai_prompt_agent.video_generation_agent()
title = ai_prompt_agent.ai_title_prompt()

print(video)
print('*'*18)
print(title)



# view_data = SaveLlmResponse()

# data = view_data.read_response()
# print(data.get('title'))