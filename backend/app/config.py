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

    # ── Firebase / Google Cloud ───────────────────────────────────────────────
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "linked-project-management")

    # ── Database mode ─────────────────────────────────────────────────────────
    # Set USE_LOCAL_DB=true in .env to use the in-memory mock (no Firebase needed)
    USE_LOCAL_DB: bool = (
        os.getenv("USE_LOCAL_DB", "false").lower() in ("true", "1", "yes")
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
        ).split(",")
        if origin.strip()
    ]

    # ── Environment mode ──────────────────────────────────────────────────────
    ENV: str = os.getenv("ENV", "development")

    # ── Groq AI (LLM extraction + transcription) ──────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ── Databricks (ML model training integration) ────────────────────────────
    DATABRICKS_HOST: str = os.getenv("DATABRICKS_HOST", "")
    DATABRICKS_TOKEN: str = os.getenv("DATABRICKS_TOKEN", "")
    DATABRICKS_CLUSTER_ID: str = os.getenv("DATABRICKS_CLUSTER_ID", "")

    # ── App metadata ──────────────────────────────────────────────────────────
    APP_NAME: str = "Linked Project Management — SIH 26122"
    APP_VERSION: str = "1.0.0"


# A single shared instance, imported everywhere else as:
#   from app.config import settings
settings = Settings()

# ── Startup key verification (printed to console on server start) ─────────────
print(f"[Config] GROQ_API_KEY: {'KEY: True [OK]' if settings.GROQ_API_KEY else 'KEY: False [WARN] -- add GROQ_API_KEY to .env'}")
print(f"[Config] Firebase credentials: {'SET [OK]' if settings.GOOGLE_APPLICATION_CREDENTIALS else 'NOT SET -- using local DB or Application Default Credentials'}")
print(f"[Config] USE_LOCAL_DB: {settings.USE_LOCAL_DB}")
print(f"[Config] Databricks token: {'SET [OK]' if settings.DATABRICKS_TOKEN else 'NOT SET'}")
