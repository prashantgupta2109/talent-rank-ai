"""Database connection and session management using SQLAlchemy 2.0 with resilient fallback."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

db_url = settings.DATABASE_URL
engine_args = {"echo": settings.DEBUG}

if "sqlite" in db_url:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_pre_ping"] = True

try:
    engine = create_engine(db_url, **engine_args)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning(
        "Could not connect to PostgreSQL at '%s'. Falling back to local SQLite database for development/testing: %s",
        db_url,
        str(e),
    )
    fallback_url = "sqlite:///./resume_matcher_dev.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False}, echo=settings.DEBUG)

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
    # Import all models to ensure metadata registration
    import app.models.entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
