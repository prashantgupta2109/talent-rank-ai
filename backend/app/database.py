"""Database connection and session management using SQLAlchemy 2.0 with bulletproof fallback."""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

raw_db_url = os.environ.get("DATABASE_URL", "").strip()

# If DATABASE_URL is not set or points to localhost in cloud environment, default cleanly to SQLite
if not raw_db_url or "localhost" in raw_db_url or "127.0.0.1" in raw_db_url:
    # Use SQLite for standalone/cloud deployments without separate Postgres
    db_url = "sqlite:///./resume_matcher.db"
else:
    db_url = raw_db_url
    # Fix Render/Heroku postgres:// URI scheme for SQLAlchemy 2.0
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine_args = {"echo": settings.DEBUG}
if "sqlite" in db_url:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_pre_ping"] = True

try:
    engine = create_engine(db_url, **engine_args)
    if "sqlite" not in db_url:
        with engine.connect() as conn:
            pass
except Exception as e:
    logger.warning("Could not connect to external DB (%s). Defaulting to SQLite: %s", db_url, str(e))
    db_url = "sqlite:///./resume_matcher.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, echo=settings.DEBUG)

# SQLAlchemy 2.0 Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    import app.models.entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
