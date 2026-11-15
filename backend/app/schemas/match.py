"""Pydantic schemas for candidate matching results, scoring breakdown, and ranking."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SemanticSkillMatch(BaseModel):
    """Details of a semantic skill match exceeding the similarity threshold."""

    jd_skill: str = Field(description="Skill requested in Job Description")
    resume_skill: str = Field(description="Corresponding skill found on candidate resume")
    similarity: float = Field(description="Cosine similarity score (0.0 to 1.0)")


class EvidenceChunk(BaseModel):
    """Top contextual resume snippet supporting alignment with a specific JD requirement."""

    jd_requirement: str = Field(description="Requirement sentence or duty from the JD")
    resume_snippet: str = Field(description="Most relevant matching snippet from the resume")
    similarity_score: float = Field(description="Cosine similarity score (0.0 to 1.0)")


class ExperienceComparison(BaseModel):
    """Comparative analysis of candidate experience versus JD requirement."""

    candidate_years: float = Field(description="Candidate's total non-overlapping experience")
    required_years: float = Field(description="Minimum years required by the JD")
    difference: float = Field(description="Surplus or deficit in experience years")
    meets_requirement: bool = Field(description="Whether candidate meets or exceeds requirement")


class EducationComparison(BaseModel):
    """Comparative analysis of candidate academic qualifications."""

    candidate_degrees: List[str] = Field(default_factory=list, description="Degrees held by candidate")
    required_degrees: List[str] = Field(default_factory=list, description="Degrees required or preferred by JD")
    meets_requirement: bool = Field(default=True, description="Whether education criteria are satisfied")


class MatchResult(BaseModel):
    """Complete scoring breakdown and explainability metadata for a candidate match."""

    candidate_name: str = Field(default="Candidate", description="Candidate name")
    candidate_id: Optional[int] = Field(default=None, description="Candidate resume ID")
    job_id: Optional[int] = Field(default=None, description="Job description ID")
    
    # Composite and component scores (0 - 100)
    overall_score: float = Field(description="Weighted overall matching percentage (0 to 100)")
    skill_score: float = Field(description="Skill overlap score (0 to 100)")
    semantic_score: float = Field(description="Semantic requirement alignment score (0 to 100)")
    experience_score: float = Field(description="Experience duration and relevance score (0 to 100)")
    education_score: float = Field(description="Educational qualification score (0 to 100)")

    # Qualitative details
    matched_skills: List[str] = Field(default_factory=list, description="Exact matched skills")
    semantically_matched_skills: List[SemanticSkillMatch] = Field(
        default_factory=list,
        description="Skills matched via semantic embedding similarity",
    )
    missing_skills: List[str] = Field(default_factory=list, description="Required or preferred skills not found")
    
    # Comparisons
    experience_comparison: ExperienceComparison
    education_comparison: EducationComparison
    top_evidence_chunks: List[EvidenceChunk] = Field(default_factory=list, description="Top evidence snippets")
    
    # Natural language explanations
    reasons: List[str] = Field(default_factory=list, description="Plain-English justification bullet points")


class MatchRankingItem(BaseModel):
    """Summary record for candidate ranking leaderboard table."""

    candidate_id: int
    candidate_name: str
    experience_years: float
    overall_score: float
    skill_score: float
    semantic_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    filename: Optional[str] = None


class BatchMatchResponse(BaseModel):
    """Response containing ranked candidates for a given job description."""

    job_id: int
    job_title: str
    total_candidates: int
    rankings: List[MatchRankingItem]
    detailed_results: List[MatchResult]
