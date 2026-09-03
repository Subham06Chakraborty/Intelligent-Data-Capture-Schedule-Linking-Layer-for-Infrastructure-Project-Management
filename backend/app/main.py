"""
app/main.py
-----------
Entry point for the FastAPI application.

Run it from the `backend/` folder with:

    uvicorn app.main:app --reload --port 8000

Then visit:
    http://localhost:8000            -> root endpoint
    http://localhost:8000/docs       -> Swagger UI
    http://localhost:8000/api/health -> health check
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health

# ---------------------------------------------------------------------------
# Logging setup (Milestone 1: just basic console logging)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sih26122")

# ---------------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend for SIH 26122 - Intelligent Data Capture & Schedule-Linking "
        "Layer for Infrastructure Project Management."
    ),
)

# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------
# In development, only the frontend origins listed in ALLOWED_ORIGINS
# (see app/config.py, sourced from the .env file) are allowed to call this
# API from a browser. Do NOT switch this to allow_origins=["*"] in a real
# deployment - that would let any website call your API on a user's behalf.
if settings.ENV == "development":
    logger.info("Running in DEVELOPMENT mode. Allowed origins: %s", settings.ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
# Each feature area of the API lives in its own router file under
# app/routes/. As we build later milestones, we will add:
#   app.include_router(projects.router)
#   app.include_router(schedules.router)
#   app.include_router(reports.router)
#   app.include_router(matching.router)
#   app.include_router(progress.router)
app.include_router(health.router)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    """Simple landing endpoint so visiting http://localhost:8000 shows
    something useful instead of a 404."""
    return {
        "message": f"{settings.APP_NAME} is running.",
        "docs": "/docs",
        "health": "/api/health",
    }
