"""FastAPI Application entrypoint."""

from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.api import jobs, resumes, matching, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    # Initialize database tables on application startup
    try:
        init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Based Resume Matching & Ranking System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount health check endpoint directly at root level
app.include_router(health.router, tags=["Health"])

# Mount API V1 route handlers
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["Jobs"])
app.include_router(resumes.router, prefix=f"{settings.API_V1_PREFIX}/resumes", tags=["Resumes"])
app.include_router(matching.router, prefix=f"{settings.API_V1_PREFIX}/matching", tags=["Matching"])

# Also mount root level routes matching Phase 4 prompt specifications (/jobs, /candidates)
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs Root"])
app.include_router(resumes.candidates_router, prefix="/candidates", tags=["Candidates Root"])


@app.get("/", tags=["Root"])
def root_summary() -> Dict[str, str]:
    """Return welcome message and documentation link."""
    return {
        "message": "Welcome to AI Resume Matching & Ranking System API",
        "docs_url": "/docs",
        "health_url": "/health",
    }
