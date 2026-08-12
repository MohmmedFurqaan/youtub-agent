import os
from dotenv import load_dotenv


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"{var_name} is not set. Add it to your environment or .env file.")
    return value


def load_all_env() -> list:
    '''
    Load the environment secrets from the .env file.
    Returns a list with the OpenRouter key, DEVMODE flag, model name,
    and the YouTube OAuth config dict.
    '''
    load_dotenv()
    envs: list = []

    OPENROUTER_API_KEY = _required_env("OPENROUTER_API_KEY")
    DEVMODE = _parse_bool(os.getenv("DEVMODE"))
    OPENROUTER_MODEL_NAME = _required_env("OPENROUTER_MODEL_NAME")
    KIE_API_KEY = os.getenv("KIE_API_KEY", "")

    youtube_config = {
        "installed": {
            "client_id": _required_env("YOUTUBE_CLIENT_ID"),
            "client_secret": _required_env("YOUTUBE_CLIENT_SECRET"),
            "project_id": _required_env("YOUTUBE_PROJECT_ID"),
            "auth_uri": os.getenv("YOUTUBE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("YOUTUBE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv(
                "YOUTUBE_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs",
            ),
            "redirect_uris": [os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost")],
        }
    }

    envs.extend([
        OPENROUTER_API_KEY,
        DEVMODE,
        OPENROUTER_MODEL_NAME,
        youtube_config,
        KIE_API_KEY,
    ])
    return envs
