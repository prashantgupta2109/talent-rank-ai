"""Resume upload and candidate detail endpoints with SQLAlchemy 2.0 persistence."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import Candidate, MatchResultRecord, JobDescription

router = APIRouter()
candidates_router = APIRouter()


@candidates_router.get("/{candidate_id}", response_model=Dict[str, Any])
def get_candidate_by_id(candidate_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full candidate profile and comprehensive match analysis for Module 5."""
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found.",
        )

    # Fetch latest match result for candidate
    stmt = (
        select(MatchResultRecord, JobDescription)
        .join(JobDescription, MatchResultRecord.job_id == JobDescription.id)
        .where(MatchResultRecord.candidate_id == candidate_id)
        .order_by(desc(MatchResultRecord.created_at))
    )
    match_row = db.execute(stmt).first()

    match_analysis = None
    if match_row:
        match_rec, job = match_row
        details = match_rec.details or {}
        match_analysis = {
            "job_id": job.id,
            "job_title": job.title,
            "overall_score": match_rec.overall_score,
            "skill_score": match_rec.skill_score,
            "semantic_score": match_rec.semantic_score,
            "experience_score": match_rec.experience_score,
            "education_score": match_rec.education_score,
            "matched_skills": match_rec.matched_skills,
            "missing_skills": match_rec.missing_skills,
            "reasons": match_rec.reasons,
            "semantically_matched_skills": details.get("semantically_matched_skills", []),
            "top_evidence_chunks": details.get("top_evidence_chunks", []),
            "experience_comparison": details.get("experience_comparison"),
            "education_comparison": details.get("education_comparison"),
            "evaluated_at": match_rec.created_at.isoformat(),
        }

    return {
        "id": cand.id,
        "name": cand.name,
        "email": cand.email,
        "phone": cand.phone,
        "filename": cand.filename,
        "total_years_experience": cand.total_years_experience,
        "skills": cand.skills,
        "work_experience": cand.work_experience,
        "education": cand.education,
        "warnings": cand.warnings,
        "match_analysis": match_analysis,
        "created_at": cand.created_at.isoformat(),
    }


@router.get("/", response_model=List[Dict[str, Any]])
def list_all_candidates(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all candidates saved across all batches."""
    stmt = select(Candidate).order_by(desc(Candidate.created_at))
    cands = db.scalars(stmt).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "total_years_experience": c.total_years_experience,
            "skills": c.skills,
            "filename": c.filename,
            "created_at": c.created_at.isoformat(),
        }
        for c in cands
    ]


@router.get("/{candidate_id}", response_model=Dict[str, Any])
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Redirect to standard candidate retrieval."""
    return get_candidate_by_id(candidate_id=candidate_id, db=db)
