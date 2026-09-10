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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

from app.config import settings
from app.routes import health, projects, ai_ingestion, ai_activities, predictions

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
# Rate Limiting Middleware (Security)
# ---------------------------------------------------------------------------
request_counts = defaultdict(list)
RATE_LIMIT = 15  # Max 15 requests per minute
RATE_WINDOW = 60  # seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only apply rate limiting to the high-compute AI ingestion endpoints
    if request.url.path.startswith("/api/v1/ingest"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up requests outside the sliding window
        request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < RATE_WINDOW]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            logger.warning("Rate limit exceeded for IP %s", client_ip)
            return JSONResponse(
                status_code=429, 
                content={"detail": "Too many requests. Please try again later."}
            )
            
        request_counts[client_ip].append(now)
        
    return await call_next(request)

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
app.include_router(projects.router)
app.include_router(ai_ingestion.router)
app.include_router(ai_activities.router)
app.include_router(predictions.router)

# Mount with /api/v1 prefix for frontend API compatibility
app.include_router(ai_ingestion.router, prefix="/api/v1")
app.include_router(ai_activities.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")



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
