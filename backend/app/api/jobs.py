"""Job description and job-centric resume workflow API endpoints with SQLAlchemy 2.0 persistence."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import JobDescription, Batch, Candidate, MatchResultRecord
from app.schemas.job import JobCreateRequest, ParsedJobDescription
from app.schemas.resume import ParsedResume
from app.schemas.match import MatchRankingItem, MatchResult
from app.services.jd_parser import parse_job_description
from app.services.resume_parser import parse_resume_file
from app.services.scorer import calculate_match

router = APIRouter()
_THREAD_POOL = ThreadPoolExecutor(max_workers=8)

# Allowed file extensions and size constraints
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Parse and persist a new Job Description into the database."""
    if not payload.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty.",
        )

    parsed = parse_job_description(payload.raw_text)
    job_title = payload.title.strip() if payload.title else parsed.title

    job = JobDescription(
        title=job_title,
        raw_text=payload.raw_text,
        required_skills=parsed.required_skills,
        preferred_skills=parsed.preferred_skills,
        min_years_experience=parsed.min_years_experience,
        education_requirements=parsed.education_requirements,
        responsibilities=parsed.responsibilities,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "id": job.id,
        "title": job.title,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "min_years_experience": job.min_years_experience,
        "education_requirements": job.education_requirements,
        "responsibilities": job.responsibilities,
        "created_at": job.created_at.isoformat(),
    }


@router.get("/", response_model=List[Dict[str, Any]])
def list_jobs(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all saved job descriptions ordered by newest first."""
    stmt = select(JobDescription).order_by(desc(JobDescription.created_at))
    jobs = db.scalars(stmt).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "required_skills": j.required_skills,
            "preferred_skills": j.preferred_skills,
            "min_years_experience": j.min_years_experience,
            "education_requirements": j.education_requirements,
            "responsibilities": j.responsibilities,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


@router.post("/parse", response_model=ParsedJobDescription)
def parse_job_preview(payload: JobCreateRequest) -> ParsedJobDescription:
    """Parse a job description for preview without saving it."""
    if not payload.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty.",
        )
    return parse_job_description(payload.raw_text)


@router.get("/{job_id}", response_model=Dict[str, Any])
def get_job(job_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve a single saved job description by ID."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found.",
        )
    return {
        "id": job.id,
        "title": job.title,
        "raw_text": job.raw_text,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "min_years_experience": job.min_years_experience,
        "education_requirements": job.education_requirements,
        "responsibilities": job.responsibilities,
        "created_at": job.created_at.isoformat(),
    }


def _parse_single_file_sync(content: bytes, filename: str) -> Dict[str, Any]:
    """Synchronous worker function to parse a resume document in a thread pool."""
    try:
        parsed = parse_resume_file(content, filename=filename)
        return {"success": True, "parsed": parsed, "error": None}
    except Exception as e:
        return {"success": False, "parsed": None, "error": str(e)}


@router.post("/{job_id}/resumes", status_code=status.HTTP_201_CREATED)
async def upload_job_resumes(
    job_id: int,
    files: List[UploadFile] = File(..., description="Multipart batch of 10+ resume files"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Upload and process a batch of candidate resumes concurrently for a specific job.

    - Validates file extensions (.pdf, .docx)
    - Validates file size limits (< 15 MB)
    - Concurrently extracts text, skills, and experience intervals
    - Groups upload session in a Batch entity
    - Returns per-file success/failure report
    """
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found.",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume files were provided.",
        )

    # 1. Read files and validate extension and size
    file_payloads: List[Dict[str, Any]] = []
    file_reports: List[Dict[str, Any]] = []

    for file in files:
        fn = file.filename or "unknown"
        ext = "." + fn.rsplit(".", 1)[-1].lower() if "." in fn else ""

        if ext not in ALLOWED_EXTENSIONS:
            file_reports.append({
                "filename": fn,
                "success": False,
                "candidate_id": None,
                "error": f"Unsupported file type '{ext}'. Allowed formats: PDF (.pdf), Word (.docx, .doc)",
            })
            continue

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            file_reports.append({
                "filename": fn,
                "success": False,
                "candidate_id": None,
                "error": f"File size ({len(content) / (1024*1024):.1f} MB) exceeds maximum limit of 15 MB.",
            })
            continue

        file_payloads.append({"filename": fn, "content": content})

    # 2. Concurrently process valid files in thread pool
    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(_THREAD_POOL, _parse_single_file_sync, item["content"], item["filename"])
        for item in file_payloads
    ]
    parsed_results = await asyncio.gather(*tasks)

    # 3. Create Batch record
    batch = Batch(
        job_id=job_id,
        name=f"Batch Upload ({len(files)} files)",
        total_files=len(files),
    )
    db.add(batch)
    db.flush()

    # 4. Save successful candidates to DB
    for item, parse_res in zip(file_payloads, parsed_results):
        fn = item["filename"]
        if parse_res["success"] and parse_res["parsed"] is not None:
            p: ParsedResume = parse_res["parsed"]
            candidate = Candidate(
                batch_id=batch.id,
                name=p.candidate_name,
                email=p.email,
                phone=p.phone,
                skills=p.skills,
                total_years_experience=p.total_years_experience,
                work_experience=[w.model_dump() for w in p.work_experience],
                education=[e.model_dump() for e in p.education],
                raw_text=p.raw_text,
                filename=fn,
                warnings=p.warnings,
            )
            db.add(candidate)
            db.flush()

            file_reports.append({
                "filename": fn,
                "success": True,
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "experience_years": candidate.total_years_experience,
                "skills_count": len(candidate.skills),
                "warnings": candidate.warnings,
                "error": None,
            })
        else:
            file_reports.append({
                "filename": fn,
                "success": False,
                "candidate_id": None,
                "error": parse_res["error"] or "Failed to parse document text",
            })

    db.commit()

    total_success = sum(1 for r in file_reports if r["success"])
    total_failed = len(file_reports) - total_success

    return {
        "batch_id": batch.id,
        "job_id": job_id,
        "total_uploaded": len(files),
        "total_successful": total_success,
        "total_failed": total_failed,
        "files": file_reports,
    }


@router.post("/{job_id}/match", status_code=status.HTTP_200_OK)
def match_job_candidates(job_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Execute AI matching algorithm across all candidates uploaded for this job."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found.",
        )

    # Find candidates associated with batches for this job
    stmt = (
        select(Candidate)
        .join(Batch, Candidate.batch_id == Batch.id)
        .where(Batch.job_id == job_id)
    )
    candidates = db.scalars(stmt).all()

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No candidates found for Job {job_id}. Please upload resumes first.",
        )

    parsed_jd = ParsedJobDescription(
        title=job.title,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_years_experience=job.min_years_experience,
        education_requirements=job.education_requirements,
        responsibilities=job.responsibilities,
        raw_text=job.raw_text,
    )

    rankings: List[Dict[str, Any]] = []

    for cand in candidates:
        parsed_resume = ParsedResume(
            candidate_name=cand.name,
            email=cand.email,
            phone=cand.phone,
            skills=cand.skills,
            total_years_experience=cand.total_years_experience,
            raw_text=cand.raw_text,
            filename=cand.filename,
        )

        match_res = calculate_match(
            jd=parsed_jd,
            resume=parsed_resume,
            candidate_id=cand.id,
            job_id=job.id,
        )

        # Check if match result already exists, update or insert
        stmt_exist = select(MatchResultRecord).where(
            MatchResultRecord.job_id == job.id,
            MatchResultRecord.candidate_id == cand.id,
        )
        existing_record = db.scalars(stmt_exist).first()

        details_dict = {
            "semantically_matched_skills": [s.model_dump() for s in match_res.semantically_matched_skills],
            "top_evidence_chunks": [e.model_dump() for e in match_res.top_evidence_chunks],
            "experience_comparison": match_res.experience_comparison.model_dump(),
            "education_comparison": match_res.education_comparison.model_dump(),
        }

        if existing_record:
            existing_record.overall_score = match_res.overall_score
            existing_record.skill_score = match_res.skill_score
            existing_record.semantic_score = match_res.semantic_score
            existing_record.experience_score = match_res.experience_score
            existing_record.education_score = match_res.education_score
            existing_record.matched_skills = match_res.matched_skills
            existing_record.missing_skills = match_res.missing_skills
            existing_record.reasons = match_res.reasons
            existing_record.details = details_dict
        else:
            new_record = MatchResultRecord(
                job_id=job.id,
                candidate_id=cand.id,
                overall_score=match_res.overall_score,
                skill_score=match_res.skill_score,
                semantic_score=match_res.semantic_score,
                experience_score=match_res.experience_score,
                education_score=match_res.education_score,
                matched_skills=match_res.matched_skills,
                missing_skills=match_res.missing_skills,
                reasons=match_res.reasons,
                details=details_dict,
            )
            db.add(new_record)

        all_matched_skills = match_res.matched_skills + [
            s.resume_skill for s in match_res.semantically_matched_skills
        ]

        rankings.append({
            "candidate_id": cand.id,
            "candidate_name": cand.name,
            "experience_years": cand.total_years_experience,
            "overall_score": match_res.overall_score,
            "skill_score": match_res.skill_score,
            "semantic_score": match_res.semantic_score,
            "matched_skills": all_matched_skills,
            "missing_skills": match_res.missing_skills,
            "filename": cand.filename,
        })

    db.commit()

    # Sort descending by overall match score
    rankings.sort(key=lambda x: x["overall_score"], reverse=True)

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_matched": len(rankings),
        "rankings": rankings,
    }


@router.get("/{job_id}/rankings", response_model=List[Dict[str, Any]])
def get_job_rankings(job_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve ranked candidate leaderboard table for Module 4."""
    job = db.get(JobDescription, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_id} not found.",
        )

    stmt = (
        select(MatchResultRecord, Candidate)
        .join(Candidate, MatchResultRecord.candidate_id == Candidate.id)
        .where(MatchResultRecord.job_id == job_id)
        .order_by(desc(MatchResultRecord.overall_score))
    )
    records = db.execute(stmt).all()

    leaderboard = []
    for match_rec, cand in records:
        details = match_rec.details or {}
        sem_skills = details.get("semantically_matched_skills", [])
        all_matched = list(match_rec.matched_skills or []) + [
            s.get("resume_skill") for s in sem_skills if isinstance(s, dict) and s.get("resume_skill")
        ]

        leaderboard.append({
            "candidate_id": cand.id,
            "candidate_name": cand.name,
            "experience_years": cand.total_years_experience,
            "overall_score": match_rec.overall_score,
            "skill_score": match_rec.skill_score,
            "semantic_score": match_rec.semantic_score,
            "experience_score": match_rec.experience_score,
            "education_score": match_rec.education_score,
            "matched_skills": all_matched,
            "missing_skills": match_rec.missing_skills or [],
            "filename": cand.filename,
            "created_at": match_rec.created_at.isoformat(),
        })

    return leaderboard
