import os 
from dotenv import load_dotenv

def load_all_env() -> list:
    '''
    Load the envirnoment secret from the .env file 
    '''
    load_dotenv()
    envs: list = []

    # Loading up all the ENV variable
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    envs.append(OPENROUTER_API_KEY)
    return envs
