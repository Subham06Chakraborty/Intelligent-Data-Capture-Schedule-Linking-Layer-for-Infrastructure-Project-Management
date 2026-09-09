"""
config.py
---------
Central place where we load settings from environment variables (.env file).

Why this file exists:
- We never want to scatter `os.getenv(...)` calls all over the codebase.
- Every other file should import `settings` from here instead of reading
  environment variables directly.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file into the process environment.
# This looks for a file named ".env" in the current working directory
# (i.e. the "backend/" folder when you run uvicorn from there).
load_dotenv()


class Settings:
    """Simple settings container. Values come from environment variables,
    with safe defaults for local development only."""

    # Firestore / Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # CORS - comma separated list of allowed frontend origins
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
        ).split(",")
        if origin.strip()
    ]

    # Environment mode
    ENV: str = os.getenv("ENV", "development")

    # App metadata
    APP_NAME: str = "SIH 26122 FastAPI Backend"
    APP_VERSION: str = "0.1.0"


# A single shared instance, imported everywhere else as:
#   from app.config import settings
settings = Settings()
