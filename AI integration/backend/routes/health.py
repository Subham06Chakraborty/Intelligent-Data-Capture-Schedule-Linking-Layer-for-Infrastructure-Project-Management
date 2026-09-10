"""
routes/health.py
-----------------
A tiny router with a single endpoint: GET /api/health

This is used to confirm the backend is running before we build anything
else. The frontend (or Swagger UI) should call this first.
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    """Returns a simple status payload so callers know the API is alive."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
    }
