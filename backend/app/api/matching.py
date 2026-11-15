"""Candidate matching and ranking API endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import Batch, Candidate, JobDescription
from app.schemas.match import MatchResult, MatchRankingItem, BatchMatchResponse
from app.schemas.job import ParsedJobDescription
from app.schemas.resume import ParsedResume
from app.services.scorer import calculate_match

router = APIRouter()

# In-memory cache for computed match results
# key: f"{job_id}_{candidate_id}" -> MatchResult dict
_MATCH_RESULTS_CACHE: Dict[str, Dict[str, Any]] = {}


def _to_parsed_job(job: JobDescription) -> ParsedJobDescription:
    return ParsedJobDescription(
        title=job.title,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_years_experience=job.min_years_experience,
        education_requirements=job.education_requirements,
        responsibilities=job.responsibilities,
        raw_text=job.raw_text,
    )


def _to_parsed_resume(candidate: Candidate) -> ParsedResume:
    return ParsedResume(
        candidate_name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        skills=candidate.skills,
        total_years_experience=candidate.total_years_experience,
        work_experience=candidate.work_experience,
        education=candidate.education,
        raw_text=candidate.raw_text,
        warnings=candidate.warnings,
        filename=candidate.filename,
    )


class MatchRequest(BaseModel):
    """Payload to trigger matching against uploaded resumes."""

    job_id: int = Field(description="ID of the job description to match against")
    resume_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of specific resume IDs. If omitted, matches all uploaded resumes.",
    )


class DirectMatchRequest(BaseModel):
    """Payload for on-the-fly direct matching without pre-saving."""

    job_description: ParsedJobDescription
    resume: ParsedResume


@router.post("/compare", response_model=BatchMatchResponse, status_code=status.HTTP_200_OK)
def compare_job_and_resumes(
    payload: MatchRequest,
    db: Session = Depends(get_db),
) -> BatchMatchResponse:
    """Compare a job description against uploaded resumes, rank them, and return full leaderboard."""
    job = db.get(JobDescription, payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {payload.job_id} not found.",
        )

    parsed_jd = _to_parsed_job(job)

    stmt = select(Candidate).join(Batch, Candidate.batch_id == Batch.id).where(
        Batch.job_id == payload.job_id
    )
    if payload.resume_ids is not None:
        stmt = stmt.where(Candidate.id.in_(payload.resume_ids))
    target_resumes = db.scalars(stmt).all()

    if not target_resumes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidate resumes found to compare. Please upload resumes first.",
        )

    rankings: List[MatchRankingItem] = []
    detailed_results: List[MatchResult] = []

    for candidate in target_resumes:
        candidate_id = candidate.id
        parsed_resume = _to_parsed_resume(candidate)

        match_res = calculate_match(
            jd=parsed_jd,
            resume=parsed_resume,
            candidate_id=candidate_id,
            job_id=payload.job_id,
        )

        cache_key = f"{payload.job_id}_{candidate_id}"
        _MATCH_RESULTS_CACHE[cache_key] = match_res.model_dump()

        detailed_results.append(match_res)

        rankings.append(
            MatchRankingItem(
                candidate_id=candidate_id or 0,
                candidate_name=match_res.candidate_name,
                experience_years=parsed_resume.total_years_experience,
                overall_score=match_res.overall_score,
                skill_score=match_res.skill_score,
                semantic_score=match_res.semantic_score,
                matched_skills=match_res.matched_skills + [
                    s.resume_skill for s in match_res.semantically_matched_skills
                ],
                missing_skills=match_res.missing_skills,
                filename=candidate.filename,
            )
        )

    # Sort rankings descending by overall_score
    rankings.sort(key=lambda r: r.overall_score, reverse=True)
    detailed_results.sort(key=lambda d: d.overall_score, reverse=True)

    return BatchMatchResponse(
        job_id=payload.job_id,
        job_title=parsed_jd.title,
        total_candidates=len(rankings),
        rankings=rankings,
        detailed_results=detailed_results,
    )


@router.get("/{job_id}/candidate/{candidate_id}", response_model=MatchResult)
def get_candidate_analysis(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
) -> MatchResult:
    """Retrieve detailed candidate-level match analysis, scores, and natural language explanations."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found.",
        )

    stmt = (
        select(Candidate)
        .join(Batch, Candidate.batch_id == Batch.id)
        .where(Batch.job_id == job_id, Candidate.id == candidate_id)
    )
    candidate = db.scalars(stmt).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match record for Job {job_id} and Candidate {candidate_id} not found.",
        )

    cache_key = f"{job_id}_{candidate_id}"
    cached = _MATCH_RESULTS_CACHE.get(cache_key)

    if cached:
        return MatchResult(**cached)

    match_res = calculate_match(
        jd=_to_parsed_job(job),
        resume=_to_parsed_resume(candidate),
        candidate_id=candidate_id,
        job_id=job_id,
    )

    _MATCH_RESULTS_CACHE[cache_key] = match_res.model_dump()
    return match_res


@router.post("/direct", response_model=MatchResult)
def direct_match(payload: DirectMatchRequest) -> MatchResult:
    """On-the-fly candidate evaluation without persisting records."""
    return calculate_match(
        jd=payload.job_description,
        resume=payload.resume,
    )
