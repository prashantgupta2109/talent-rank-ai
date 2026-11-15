"""Unit tests for Resume Parser and interval merging calculations."""

import pytest
from app.services.resume_parser import (
    parse_resume_file,
    _calculate_merged_experience,
    _parse_date_string,
)

SAMPLE_RESUME_TEXT = """
Alex Mercer
alex.mercer@gmail.com | (415) 555-0192 | San Francisco, CA

Professional Summary:
Senior ML Engineer with 6 years experience building large-scale NLP microservices.

Technical Skills:
Python, PyTorch, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, scikit-learn

Work Experience:
Lead Machine Learning Engineer | NeuralScale AI | Jan 2021 - Present
- Designed RAG pipelines with FastAPI and ChromaDB.

Senior ML Engineer | Apex Data Labs | Mar 2018 - Dec 2020
- Built classification services with scikit-learn, spaCy, and PostgreSQL.

Education:
Ph.D. in Computer Science | Stanford University | 2018
Bachelor of Science in Mathematics | UC Berkeley | 2014
"""


def test_resume_text_parsing():
    """Verify name, contact details, skills, and experience extraction from text."""
    parsed = parse_resume_file(SAMPLE_RESUME_TEXT.encode("utf-8"), filename="alex_resume.txt")

    assert parsed.candidate_name == "Alex Mercer"
    assert parsed.email == "alex.mercer@gmail.com"
    assert "(415) 555-0192" in parsed.phone

    # Skills check
    assert "Python" in parsed.skills
    assert "PyTorch" in parsed.skills
    assert "FastAPI" in parsed.skills
    assert "Docker" in parsed.skills
    assert "PostgreSQL" in parsed.skills

    # Experience duration check (2018 to present should be >= 5.5 years)
    assert parsed.total_years_experience >= 5.0
    assert len(parsed.work_experience) >= 2

    # Education check
    assert len(parsed.education) >= 1
    degrees = [e.degree.lower() for e in parsed.education]
    assert any("ph.d" in d or "doctorate" in d or "bachelor" in d for d in degrees)


def test_overlapping_experience_merging():
    """Verify that overlapping job date ranges do not double-count experience."""
    # Case 1: Job A (2018.0 - 2021.0 = 3 yrs) and Job B (2020.0 - 2022.0 = 2 yrs)
    # Merged interval should be 2018.0 to 2022.0 = 4.0 years (not 5.0)
    intervals = [(2018.0, 2021.0), (2020.0, 2022.0)]
    total = _calculate_merged_experience(intervals)
    assert total == 4.0

    # Case 2: Completely disjoint intervals (2016 - 2018 = 2 yrs) and (2020 - 2023 = 3 yrs) => 5.0 yrs
    intervals_disjoint = [(2016.0, 2018.0), (2020.0, 2023.0)]
    assert _calculate_merged_experience(intervals_disjoint) == 5.0

    # Case 3: Fully contained interval: Job A (2018 - 2023 = 5 yrs), Job B (2019 - 2021 = 2 yrs) => 5.0 yrs
    intervals_contained = [(2018.0, 2023.0), (2019.0, 2021.0)]
    assert _calculate_merged_experience(intervals_contained) == 5.0


def test_empty_or_malformed_file_handling():
    """Verify graceful handling with non-fatal warnings instead of crashing."""
    parsed_empty = parse_resume_file(b"", filename="empty.pdf")
    assert len(parsed_empty.warnings) > 0
    assert parsed_empty.total_years_experience == 0.0

    parsed_corrupt = parse_resume_file(b"NOT A REAL PDF CONTENT", filename="corrupt.pdf")
    # Should not raise exception, but return warnings
    assert isinstance(parsed_corrupt.warnings, list)
