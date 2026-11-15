"""SQLAlchemy 2.0 ORM models for Job Descriptions, Batches, Candidates, and Match Results."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class JobDescription(Base):
    """Job Description entity with structured parsing metadata."""

    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), default="Software Engineer", index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    min_years_experience: Mapped[float] = mapped_column(Float, default=0.0)
    education_requirements: Mapped[List[str]] = mapped_column(JSON, default=list)
    responsibilities: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="job", cascade="all, delete-orphan")
    match_results: Mapped[List["MatchResultRecord"]] = relationship(
        "MatchResultRecord", back_populates="job", cascade="all, delete-orphan"
    )


class Batch(Base):
    """Batch session grouping uploaded resumes for a job."""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="Upload Batch")
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    job: Mapped["JobDescription"] = relationship("JobDescription", back_populates="batches")
    candidates: Mapped[List["Candidate"]] = relationship(
        "Candidate", back_populates="batch", cascade="all, delete-orphan"
    )


class Candidate(Base):
    """Extracted candidate resume entity."""

    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Candidate", index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    total_years_experience: Mapped[float] = mapped_column(Float, default=0.0)
    work_experience: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    education: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    warnings: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="candidates")
    match_results: Mapped[List["MatchResultRecord"]] = relationship(
        "MatchResultRecord", back_populates="candidate", cascade="all, delete-orphan"
    )


class MatchResultRecord(Base):
    """Persisted candidate evaluation record against a specific job."""

    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[float] = mapped_column(Float, index=True)
    skill_score: Mapped[float] = mapped_column(Float)
    semantic_score: Mapped[float] = mapped_column(Float)
    experience_score: Mapped[float] = mapped_column(Float)
    education_score: Mapped[float] = mapped_column(Float)
    matched_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[List[str]] = mapped_column(JSON, default=list)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    job: Mapped["JobDescription"] = relationship("JobDescription", back_populates="match_results")
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="match_results")
