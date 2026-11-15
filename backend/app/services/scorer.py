"""Candidate matching and scoring calculation service implementing the four-factor algorithm."""

import re
from typing import Dict, List, Tuple, Set, Any, Optional
import numpy as np
from app.config import get_settings
from app.schemas.job import ParsedJobDescription
from app.schemas.resume import ParsedResume, EducationEntry
from app.schemas.match import (
    MatchResult,
    SemanticSkillMatch,
    EvidenceChunk,
    ExperienceComparison,
    EducationComparison,
)
from app.services.embedder import embed, compute_cosine_similarity
from app.services.explainer import generate_match_reasons

settings = get_settings()


def score_skills(
    required_skills: List[str],
    preferred_skills: List[str],
    candidate_skills: List[str],
    similarity_threshold: float = 0.75,
) -> Tuple[float, List[str], List[SemanticSkillMatch], List[str]]:
    """Calculate skill score (0-100) combining exact and semantic embedding matches.

    Args:
        required_skills: Mandatory JD skills (weight 1.0).
        preferred_skills: Nice-to-have JD skills (weight 0.5).
        candidate_skills: Skills extracted from the resume.
        similarity_threshold: Cosine similarity cutoff for semantic match.

    Returns:
        Tuple containing (skill_score, matched_skills, semantically_matched_skills, missing_skills)
    """
    if not required_skills and not preferred_skills:
        return 100.0, [], [], []

    candidate_skills_set = {s.lower(): s for s in candidate_skills}
    matched_exact: List[str] = []
    matched_semantic: List[SemanticSkillMatch] = []
    missing: List[str] = []

    # Prepare embedding lookups for candidate skills if needed
    cand_list = list(candidate_skills)
    cand_embeddings: Optional[np.ndarray] = None
    if cand_list:
        cand_embeddings = embed(cand_list)

    total_weight = 0.0
    earned_weight = 0.0

    # Combine required and preferred with their respective weights
    jd_skills_with_weights = [
        (s, settings.REQUIRED_SKILL_WEIGHT) for s in required_skills
    ] + [
        (s, settings.PREFERRED_SKILL_WEIGHT) for s in preferred_skills
    ]

    for jd_skill, weight in jd_skills_with_weights:
        total_weight += weight
        jd_lower = jd_skill.lower()

        # 1. Exact match check
        if jd_lower in candidate_skills_set:
            matched_exact.append(jd_skill)
            earned_weight += weight
            continue

        # 2. Semantic embedding match check against candidate skills
        found_semantic = False
        if cand_embeddings is not None and cand_embeddings.shape[0] > 0:
            jd_vec = embed([jd_skill])
            sims = compute_cosine_similarity(jd_vec, cand_embeddings)[0]
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            if best_sim >= similarity_threshold:
                matched_semantic.append(
                    SemanticSkillMatch(
                        jd_skill=jd_skill,
                        resume_skill=cand_list[best_idx],
                        similarity=round(best_sim, 3),
                    )
                )
                earned_weight += weight
                found_semantic = True

        if not found_semantic:
            missing.append(jd_skill)

    skill_score = (earned_weight / total_weight) * 100.0 if total_weight > 0 else 100.0
    return round(skill_score, 1), matched_exact, matched_semantic, missing


def _chunk_resume_text(text: str) -> List[str]:
    """Segment resume text into coherent contextual chunks for semantic matching."""
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks: List[str] = []
    for line in raw_lines:
        cleaned = re.sub(r"^[\s*•\-\d.)]+", "", line).strip()
        if len(cleaned.split()) >= 4:  # At least 4 words
            chunks.append(cleaned)
    return chunks if chunks else [text[:200]]


def score_semantic(
    jd_requirements: List[str],
    resume_text: str,
    top_k: int = 3,
) -> Tuple[float, List[EvidenceChunk]]:
    """Calculate semantic requirement alignment score (0-100) using sentence embeddings.

    Args:
        jd_requirements: Sentence-level responsibilities and requirements.
        resume_text: Raw resume document text.
        top_k: Number of highest-confidence evidence snippets to retain.

    Returns:
        Tuple containing (semantic_score, top_evidence_chunks)
    """
    if not jd_requirements or not resume_text.strip():
        return 50.0, []

    resume_chunks = _chunk_resume_text(resume_text)
    if not resume_chunks:
        return 50.0, []

    req_embeddings = embed(jd_requirements)
    chunk_embeddings = embed(resume_chunks)

    # Compute similarity matrix (len(jd_requirements) x len(resume_chunks))
    sim_matrix = compute_cosine_similarity(req_embeddings, chunk_embeddings)

    max_sims = []
    evidence_candidates: List[EvidenceChunk] = []

    for i, req in enumerate(jd_requirements):
        row = sim_matrix[i]
        best_chunk_idx = int(np.argmax(row))
        best_sim = float(row[best_chunk_idx])
        max_sims.append(best_sim)

        evidence_candidates.append(
            EvidenceChunk(
                jd_requirement=req[:120],
                resume_snippet=resume_chunks[best_chunk_idx][:160],
                similarity_score=round(best_sim, 3),
            )
        )

    # Average maximum similarities
    avg_sim = float(np.mean(max_sims)) if max_sims else 0.5

    # Rescale raw cosine similarity (typical range ~0.20 to ~0.80) to 0.0 - 100.0
    min_cos = 0.20
    max_cos = 0.80
    scaled_score = ((avg_sim - min_cos) / (max_cos - min_cos)) * 100.0
    scaled_score = max(0.0, min(100.0, scaled_score))

    # Sort evidence candidates by highest similarity score
    evidence_candidates.sort(key=lambda x: x.similarity_score, reverse=True)
    top_evidence = evidence_candidates[:top_k]

    return round(scaled_score, 1), top_evidence


def score_experience(
    candidate_years: float,
    required_years: float,
    candidate_titles: List[str] = None,
    target_job_title: str = "",
) -> Tuple[float, ExperienceComparison]:
    """Calculate experience score (0-100) based on duration cap and title match bonus.

    Args:
        candidate_years: Non-overlapping experience years of candidate.
        required_years: Minimum years required by JD.
        candidate_titles: List of past job titles held by candidate.
        target_job_title: Desired job title from JD.

    Returns:
        Tuple containing (experience_score, ExperienceComparison)
    """
    diff = round(candidate_years - required_years, 1)
    meets_req = candidate_years >= required_years

    if required_years <= 0:
        base_score = 100.0
    else:
        ratio = min(candidate_years / required_years, 1.0)
        base_score = ratio * 100.0

    # Small title match bonus (up to 10 points) if title matches target role keywords
    bonus = 0.0
    if target_job_title and candidate_titles:
        target_tokens = set(re.findall(r"\w+", target_job_title.lower())) - {
            "senior", "junior", "lead", "staff", "role", "position", "title"
        }
        for title in candidate_titles:
            past_tokens = set(re.findall(r"\w+", title.lower()))
            if target_tokens & past_tokens:
                bonus = settings.TITLE_MATCH_BONUS * 100.0
                break

    final_score = min(100.0, base_score + bonus)
    comparison = ExperienceComparison(
        candidate_years=round(candidate_years, 1),
        required_years=round(required_years, 1),
        difference=diff,
        meets_requirement=meets_req,
    )
    return round(final_score, 1), comparison


def score_education(
    candidate_education: List[EducationEntry],
    education_requirements: List[str],
) -> Tuple[float, EducationComparison]:
    """Calculate education score (0-100) based on degree hierarchy and STEM field.

    Args:
        candidate_education: Extracted degrees and fields from resume.
        education_requirements: Education criteria detected in JD.

    Returns:
        Tuple containing (education_score, EducationComparison)
    """
    deg_names = [e.degree.lower() for e in candidate_education]
    fields = [e.field_of_study.lower() for e in candidate_education if e.field_of_study]

    # Highest degree tier
    base_score = 70.0  # Default baseline for professionals
    highest_degree = "None Specified"

    if any("ph.d" in d or "doctor" in d for d in deg_names):
        base_score = 100.0
        highest_degree = "Doctorate (Ph.D.)"
    elif any("master" in d or "m.s." in d or "m.tech" in d for d in deg_names):
        base_score = 90.0
        highest_degree = "Master's Degree"
    elif any("bachelor" in d or "b.s." in d or "b.tech" in d or "b.e." in d for d in deg_names):
        base_score = 80.0
        highest_degree = "Bachelor's Degree"
    elif any("associate" in d for d in deg_names):
        base_score = 65.0
        highest_degree = "Associate Degree"

    # Field bonus (+10 if STEM / Computer Science related)
    stem_keywords = {"computer", "data", "software", "information", "mathematics", "statistics", "electrical"}
    field_match = any(any(k in f for k in stem_keywords) for f in fields)
    if field_match:
        base_score = min(100.0, base_score + 10.0)

    comparison = EducationComparison(
        candidate_degrees=[highest_degree] if highest_degree != "None Specified" else deg_names[:2],
        required_degrees=education_requirements[:2],
        meets_requirement=base_score >= 75.0,
    )
    return round(base_score, 1), comparison


def calculate_match(
    jd: ParsedJobDescription,
    resume: ParsedResume,
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
) -> MatchResult:
    """Compute overall weighted composite score and explainability metadata.

    Final Score = 0.40 × Skills + 0.30 × Semantic + 0.20 × Experience + 0.10 × Education
    """
    # 1. Skill Score
    skill_score, matched_exact, matched_semantic, missing = score_skills(
        required_skills=jd.required_skills,
        preferred_skills=jd.preferred_skills,
        candidate_skills=resume.skills,
        similarity_threshold=settings.SKILL_SIMILARITY_THRESHOLD,
    )

    # 2. Semantic Score
    jd_req_sentences = jd.responsibilities + [
        f"Requires strong practical proficiency in {', '.join(jd.required_skills[:6])}."
    ]
    semantic_score, top_evidence = score_semantic(
        jd_requirements=jd_req_sentences,
        resume_text=resume.raw_text,
    )

    # 3. Experience Score
    past_titles = [w.title for w in resume.work_experience]
    experience_score, exp_comparison = score_experience(
        candidate_years=resume.total_years_experience,
        required_years=jd.min_years_experience,
        candidate_titles=past_titles,
        target_job_title=jd.title,
    )

    # 4. Education Score
    education_score, edu_comparison = score_education(
        candidate_education=resume.education,
        education_requirements=jd.education_requirements,
    )

    # Composite weighted final score
    overall = (
        settings.WEIGHT_SKILLS * skill_score +
        settings.WEIGHT_SEMANTIC * semantic_score +
        settings.WEIGHT_EXPERIENCE * experience_score +
        settings.WEIGHT_EDUCATION * education_score
    )
    overall_score = round(max(0.0, min(100.0, overall)), 1)

    result = MatchResult(
        candidate_name=resume.candidate_name,
        candidate_id=candidate_id,
        job_id=job_id,
        overall_score=overall_score,
        skill_score=skill_score,
        semantic_score=semantic_score,
        experience_score=experience_score,
        education_score=education_score,
        matched_skills=matched_exact,
        semantically_matched_skills=matched_semantic,
        missing_skills=missing,
        experience_comparison=exp_comparison,
        education_comparison=edu_comparison,
        top_evidence_chunks=top_evidence,
        reasons=[],
    )

    # Generate plain-English explanation bullets
    result.reasons = generate_match_reasons(result)

    return result
