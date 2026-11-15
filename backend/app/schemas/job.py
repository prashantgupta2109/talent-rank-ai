"""Pydantic schemas for Job Description extraction and storage."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ParsedJobDescription(BaseModel):
    """Structured representations of an extracted Job Description."""

    title: str = Field(default="Software Engineer", description="Extracted or inferred job title")
    required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory skills extracted from required/qualifications sections",
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Nice-to-have or preferred skills",
    )
    min_years_experience: float = Field(
        default=0.0,
        description="Minimum years of professional experience required",
    )
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Degrees, fields of study, or educational criteria detected",
    )
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key duties and job responsibilities extracted from the JD",
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Original unparsed job description text",
    )


class JobCreateRequest(BaseModel):
    """Request payload to parse and save a job description."""

    title: Optional[str] = None
    raw_text: str = Field(..., min_length=10, description="Raw job description text")


class JobResponse(ParsedJobDescription):
    """Job description response with internal ID and creation timestamp."""

    id: Optional[int] = None
