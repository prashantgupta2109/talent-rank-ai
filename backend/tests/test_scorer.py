"""Unit tests for matching algorithm scoring functions and template-based explanations."""

import pytest
from app.services.scorer import (
    score_skills,
    score_semantic,
    score_experience,
    score_education,
    calculate_match,
)
from app.services.explainer import generate_match_reasons
from app.schemas.job import ParsedJobDescription
from app.schemas.resume import ParsedResume, EducationEntry, WorkExperienceEntry
from app.schemas.match import MatchResult


def test_score_skills_pure():
    """Verify exact match, weighting, and missing skill calculation."""
    required = ["Python", "FastAPI", "Docker"]  # weight 1.0 each => total 3.0
    preferred = ["Kubernetes", "AWS"]          # weight 0.5 each => total 1.0
    # Total possible weight = 4.0

    # Candidate has Python, FastAPI (required) and AWS (preferred)
    # Earned weight = 1.0 + 1.0 + 0.5 = 2.5
    # Expected skill score = (2.5 / 4.0) * 100 = 62.5%
    candidate_skills = ["Python", "FastAPI", "AWS", "Git"]

    score, exact, semantic, missing = score_skills(
        required_skills=required,
        preferred_skills=preferred,
        candidate_skills=candidate_skills,
        similarity_threshold=0.75,
    )

    assert score == 62.5
    assert "Python" in exact
    assert "FastAPI" in exact
    assert "Docker" in missing
    assert "Kubernetes" in missing


def test_score_experience_pure():
    """Verify experience ratio capping and title bonus."""
    # Case 1: Candidate meets required years (5 yrs vs 4 yrs) => 100.0
    score, comp = score_experience(candidate_years=5.0, required_years=4.0)
    assert score == 100.0
    assert comp.meets_requirement is True
    assert comp.difference == 1.0

    # Case 2: Candidate has less experience (2 yrs vs 4 yrs) => 50.0
    score_half, comp_half = score_experience(candidate_years=2.0, required_years=4.0)
    assert score_half == 50.0
    assert comp_half.meets_requirement is False
    assert comp_half.difference == -2.0

    # Case 3: Title match bonus
    score_with_bonus, _ = score_experience(
        candidate_years=2.0,
        required_years=4.0,
        candidate_titles=["Junior Machine Learning Engineer"],
        target_job_title="Machine Learning Engineer",
    )
    # 50.0 + 10.0 bonus = 60.0
    assert score_with_bonus == 60.0


def test_score_education_pure():
    """Verify degree hierarchy and STEM field bonus."""
    phd_edu = [EducationEntry(degree="Ph.D.", field_of_study="Computer Science", graduation_year=2020)]
    score_phd, comp_phd = score_education(phd_edu, ["Bachelor's Degree"])
    assert score_phd == 100.0
    assert comp_phd.meets_requirement is True

    bs_edu = [EducationEntry(degree="Bachelor of Science", field_of_study="Statistics", graduation_year=2021)]
    score_bs, comp_bs = score_education(bs_edu, ["Bachelor's Degree"])
    # 80 base + 10 STEM bonus = 90.0
    assert score_bs == 90.0


def test_full_calculate_match_strong_vs_weak():
    """Verify end-to-end composite scoring for strong vs weak candidate fits."""
    jd = ParsedJobDescription(
        title="Senior Python / ML Engineer",
        required_skills=["Python", "PyTorch", "FastAPI", "Docker", "PostgreSQL"],
        preferred_skills=["Kubernetes", "AWS"],
        min_years_experience=4.0,
        education_requirements=["Bachelor's degree in Computer Science"],
        responsibilities=[
            "Build and scale machine learning pipelines and NLP systems.",
            "Design REST APIs using FastAPI and deploy on AWS with Docker.",
        ],
    )

    strong_resume = ParsedResume(
        candidate_name="Alex Mercer",
        skills=["Python", "PyTorch", "FastAPI", "Docker", "PostgreSQL", "AWS"],
        total_years_experience=6.0,
        work_experience=[
            WorkExperienceEntry(title="Senior ML Engineer", duration_years=6.0)
        ],
        education=[
            EducationEntry(degree="Master of Science", field_of_study="Computer Science")
        ],
        raw_text="Experienced Senior ML Engineer deploying PyTorch models and FastAPI microservices on AWS.",
    )

    weak_resume = ParsedResume(
        candidate_name="Lucas Silva",
        skills=["React", "TypeScript", "HTML", "CSS"],
        total_years_experience=3.0,
        work_experience=[
            WorkExperienceEntry(title="Frontend Developer", duration_years=3.0)
        ],
        education=[
            EducationEntry(degree="Bachelor of Arts", field_of_study="Graphic Design")
        ],
        raw_text="Frontend Developer building user interfaces with React and Tailwind CSS.",
    )

    strong_result = calculate_match(jd, strong_resume)
    weak_result = calculate_match(jd, weak_resume)

    # Strong candidate should comfortably score >= 80%
    assert strong_result.overall_score >= 80.0
    assert len(strong_result.reasons) >= 3

    # Weak candidate should score much lower (<= 55%)
    assert weak_result.overall_score <= 55.0
    assert strong_result.overall_score > weak_result.overall_score + 30.0


def test_explainer_templates():
    """Verify template-based explanations are generated cleanly without LLMs."""
    jd = ParsedJobDescription(
        title="ML Engineer",
        required_skills=["Python", "PyTorch"],
        min_years_experience=3.0,
    )
    resume = ParsedResume(
        candidate_name="Test Candidate",
        skills=["Python"],
        total_years_experience=4.5,
        education=[EducationEntry(degree="Master's", field_of_study="Data Science")],
        raw_text="Python data engineer.",
    )

    result = calculate_match(jd, resume)
    reasons = generate_match_reasons(result)

    assert isinstance(reasons, list)
    assert 3 <= len(reasons) <= 5
    # Check that key factual numbers appear in the explanation
    reasons_text = " ".join(reasons)
    assert "4.5" in reasons_text or "experience" in reasons_text
    assert "Matched" in reasons_text
