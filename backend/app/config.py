"""
config.py
---------
Central place where we load settings from the backend/.env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Get the backend directory:
# backend/app/config.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load backend/.env
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)


class Settings:
    """Application settings loaded from backend/.env."""

    # Firestore / Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )

    GOOGLE_CLOUD_PROJECT: str = os.getenv(
        "GOOGLE_CLOUD_PROJECT", ""
    )

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]

    # Environment
    ENV: str = os.getenv("ENV", "development")

    # App metadata
    APP_NAME: str = "SIH 26122 FastAPI Backend"
    APP_VERSION: str = "0.1.0"


settings = Settings()