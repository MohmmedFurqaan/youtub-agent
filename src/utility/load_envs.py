import os
from dotenv import load_dotenv


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_all_env() -> list:
    '''
    Load the environment secrets from the .env file
    '''
    load_dotenv()
    envs: list = []

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DEVMODE = _parse_bool(os.getenv("DEVMODE"))
    OPENROUTER_MODEL_NAME=os.getenv("OPENROUTER_MODEL_NAME")

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your environment or .env file.")

    
    
    if not OPENROUTER_MODEL_NAME:
        raise RuntimeError("OPENROUTER MODEL NAME is not set. Add it to your environment or .env file.")
    
    envs.append(OPENROUTER_API_KEY)
    envs.append(DEVMODE)
    envs.append(OPENROUTER_MODEL_NAME)
    return envs
