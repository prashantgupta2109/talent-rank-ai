"""Pydantic schemas for Candidate Resume parsing and representation."""

from typing import List, Optional
from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    """Structured details of candidate educational history."""

    degree: str = Field(default="Degree", description="Degree or diploma level (e.g. Bachelor's, Master's)")
    institution: Optional[str] = Field(default=None, description="University, college, or institute name")
    field_of_study: Optional[str] = Field(default=None, description="Major or area of specialization")
    graduation_year: Optional[int] = Field(default=None, description="Year of graduation or completion")


class WorkExperienceEntry(BaseModel):
    """Structured details of a single employment position."""

    title: str = Field(default="Software Professional", description="Job title or role held")
    company: Optional[str] = Field(default=None, description="Company or organization name")
    start_date: Optional[str] = Field(default=None, description="Start date string (e.g. 'Jan 2020')")
    end_date: Optional[str] = Field(default=None, description="End date string (e.g. 'Present' or 'Dec 2022')")
    duration_years: float = Field(default=0.0, description="Duration in years for this position")
    description: Optional[str] = Field(default=None, description="Summary of responsibilities and achievements")


class ParsedResume(BaseModel):
    """Complete structured representation of an extracted candidate resume."""

    candidate_name: str = Field(default="Candidate", description="Detected candidate full name")
    email: Optional[str] = Field(default=None, description="Candidate contact email address")
    phone: Optional[str] = Field(default=None, description="Candidate contact phone number")
    skills: List[str] = Field(default_factory=list, description="All technical and soft skills identified")
    total_years_experience: float = Field(
        default=0.0,
        description="Non-overlapping cumulative professional experience in years",
    )
    work_experience: List[WorkExperienceEntry] = Field(
        default_factory=list,
        description="Individual chronological work experience entries",
    )
    education: List[EducationEntry] = Field(
        default_factory=list,
        description="List of degrees and academic qualifications",
    )
    raw_text: str = Field(default="", description="Cleaned raw text extracted from the document")
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during parsing (e.g. date ambiguity)",
    )
    filename: Optional[str] = Field(default=None, description="Original uploaded file name")


class ResumeResponse(ParsedResume):
    """Resume representation with persisted identifier."""

    id: Optional[int] = None
