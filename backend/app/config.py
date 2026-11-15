"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for FastAPI application and matching algorithm."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General App Settings
    PROJECT_NAME: str = "AI-Based Resume Matching & Ranking System"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/resume_matcher",
        description="Database connection string (SQLAlchemy format)",
    )

    # NLP Model Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"

    # Matching Algorithm Weights (Sum = 1.0)
    WEIGHT_SKILLS: float = Field(default=0.40, description="Weight for skill overlap score")
    WEIGHT_SEMANTIC: float = Field(default=0.30, description="Weight for semantic similarity score")
    WEIGHT_EXPERIENCE: float = Field(default=0.20, description="Weight for experience alignment score")
    WEIGHT_EDUCATION: float = Field(default=0.10, description="Weight for education qualification score")

    # Algorithm Thresholds & Multipliers
    SKILL_SIMILARITY_THRESHOLD: float = Field(
        default=0.75,
        description="Minimum cosine similarity for a resume skill to satisfy a JD skill",
    )
    REQUIRED_SKILL_WEIGHT: float = Field(
        default=1.0,
        description="Weight multiplier for mandatory JD skills",
    )
    PREFERRED_SKILL_WEIGHT: float = Field(
        default=0.5,
        description="Weight multiplier for preferred/nice-to-have JD skills",
    )
    TITLE_MATCH_BONUS: float = Field(
        default=0.10,
        description="Bonus score if candidate title matches target JD role title",
    )

    # Uploads & Limits
    UPLOAD_DIR: str = "uploads"
    MAX_BATCH_UPLOAD_SIZE: int = 50


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
