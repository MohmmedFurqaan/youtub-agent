"""
src/utility/load_envs.py

Loads environment secrets from .env.
Returns: (OPENROUTER_API_KEY, OPENROUTER_MODEL_NAME, youtube_config)

KIE_API_KEY has been removed — no text-to-video API is used.
"""

import os
from dotenv import load_dotenv


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(
            f"{var_name} is not set. Add it to your environment or .env file."
        )
    return value


def load_all_env() -> tuple[str, str, dict]:
    """Load all required environment variables.

    Returns:
        Tuple of (OPENROUTER_API_KEY, OPENROUTER_MODEL_NAME, youtube_config).
    """
    load_dotenv()

    openrouter_api_key = _required_env("OPENROUTER_API_KEY")
    openrouter_model_name = _required_env("OPENROUTER_MODEL_NAME")

    youtube_config = {
        "installed": {
            "client_id": _required_env("YOUTUBE_CLIENT_ID"),
            "client_secret": _required_env("YOUTUBE_CLIENT_SECRET"),
            "project_id": _required_env("YOUTUBE_PROJECT_ID"),
            "auth_uri": os.getenv(
                "YOUTUBE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": os.getenv(
                "YOUTUBE_TOKEN_URI", "https://oauth2.googleapis.com/token"
            ),
            "auth_provider_x509_cert_url": os.getenv(
                "YOUTUBE_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs",
            ),
            "redirect_uris": [
                os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost")
            ],
        }
    }

    return openrouter_api_key, openrouter_model_name, youtube_config
