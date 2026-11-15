"""Candidate matching and ranking API endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.schemas.match import MatchResult, MatchRankingItem, BatchMatchResponse
from app.schemas.job import ParsedJobDescription
from app.schemas.resume import ParsedResume
from app.api.jobs import _JOBS_STORE
from app.api.resumes import _RESUMES_STORE
from app.services.scorer import calculate_match

router = APIRouter()

# In-memory cache for computed match results
# key: f"{job_id}_{candidate_id}" -> MatchResult dict
_MATCH_RESULTS_CACHE: Dict[str, Dict[str, Any]] = {}


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
def compare_job_and_resumes(payload: MatchRequest) -> BatchMatchResponse:
    """Compare a job description against uploaded resumes, rank them, and return full leaderboard."""
    job_data = _JOBS_STORE.get(payload.job_id)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {payload.job_id} not found.",
        )

    parsed_jd = ParsedJobDescription(**job_data)

    target_resumes = []
    if payload.resume_ids:
        for r_id in payload.resume_ids:
            if r_id in _RESUMES_STORE:
                target_resumes.append(_RESUMES_STORE[r_id])
    else:
        target_resumes = list(_RESUMES_STORE.values())

    if not target_resumes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidate resumes found to compare. Please upload resumes first.",
        )

    rankings: List[MatchRankingItem] = []
    detailed_results: List[MatchResult] = []

    for res_data in target_resumes:
        candidate_id = res_data.get("id")
        parsed_resume = ParsedResume(**res_data)

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
                filename=res_data.get("filename"),
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
def get_candidate_analysis(job_id: int, candidate_id: int) -> MatchResult:
    """Retrieve detailed candidate-level match analysis, scores, and natural language explanations."""
    cache_key = f"{job_id}_{candidate_id}"
    cached = _MATCH_RESULTS_CACHE.get(cache_key)

    if cached:
        return MatchResult(**cached)

    job_data = _JOBS_STORE.get(job_id)
    res_data = _RESUMES_STORE.get(candidate_id)

    if not job_data or not res_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match record for Job {job_id} and Candidate {candidate_id} not found.",
        )

    match_res = calculate_match(
        jd=ParsedJobDescription(**job_data),
        resume=ParsedResume(**res_data),
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
