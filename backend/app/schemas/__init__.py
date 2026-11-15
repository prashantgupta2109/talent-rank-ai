"""Pydantic v2 schemas package for request/response serialization."""

from app.schemas.job import ParsedJobDescription, JobCreateRequest, JobResponse
from app.schemas.resume import ParsedResume, ResumeResponse, EducationEntry, WorkExperienceEntry
from app.schemas.match import (
    MatchResult,
    SemanticSkillMatch,
    EvidenceChunk,
    ExperienceComparison,
    EducationComparison,
    MatchRankingItem,
    BatchMatchResponse,
)

__all__ = [
    "ParsedJobDescription",
    "JobCreateRequest",
    "JobResponse",
    "ParsedResume",
    "ResumeResponse",
    "EducationEntry",
    "WorkExperienceEntry",
    "MatchResult",
    "SemanticSkillMatch",
    "EvidenceChunk",
    "ExperienceComparison",
    "EducationComparison",
    "MatchRankingItem",
    "BatchMatchResponse",
]
