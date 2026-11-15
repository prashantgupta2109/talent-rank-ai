"""Health check endpoint for monitoring service readiness and dependencies."""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=Dict[str, Any])
def health_check() -> Dict[str, Any]:
    """Return health status, current UTC timestamp, and service metadata."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
