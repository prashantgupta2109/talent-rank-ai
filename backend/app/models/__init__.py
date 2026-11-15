"""SQLAlchemy 2.0 ORM models package."""

from app.database import Base
from app.models.entities import JobDescription, Batch, Candidate, MatchResultRecord

__all__ = [
    "Base",
    "JobDescription",
    "Batch",
    "Candidate",
    "MatchResultRecord",
]
