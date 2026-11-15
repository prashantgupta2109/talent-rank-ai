"""Integration tests for Phase 4 API endpoints and database workflows."""

import io
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

# Initialize database tables
init_db()
client = TestClient(app)

SAMPLE_JD = """
Job Title: Python / Machine Learning Engineer

Requirements:
- 4+ years of experience with Python, PyTorch, and FastAPI.
- Hands-on experience with Docker and PostgreSQL.
- Bachelor's degree in Computer Science.

Nice to Have:
- Experience with AWS and Kubernetes.
"""

RESUME_ALEX = """
Alex Mercer
alex@example.com | (415) 555-0192

Professional Summary:
Senior ML Engineer with 6 years experience.

Technical Skills:
Python, PyTorch, FastAPI, Docker, PostgreSQL, AWS

Work Experience:
Senior ML Engineer | Apex AI | Jan 2019 - Present

Education:
Master of Science in Computer Science | 2018
"""

RESUME_LUCAS = """
Lucas Silva
lucas@example.com | (212) 555-0138

Professional Summary:
Frontend Developer with 3 years experience.

Technical Skills:
React, TypeScript, HTML, CSS

Work Experience:
Frontend Developer | WebStudio | Jan 2021 - Present

Education:
Bachelor of Arts in Design | 2020
"""


def test_full_job_candidate_match_lifecycle():
    """Verify end-to-end workflow: POST job -> upload resumes -> match -> rankings -> candidate detail."""

    # 1. Create Job Description
    job_resp = client.post("/jobs/", json={"title": "ML Engineer", "raw_text": SAMPLE_JD})
    assert job_resp.status_code == 201
    job_data = job_resp.json()
    job_id = job_data["id"]
    assert job_id is not None
    assert "Python" in job_data["required_skills"]

    # 2. Upload Batch Resumes (multipart form data)
    files = [
        ("files", ("alex_mercer.pdf", io.BytesIO(RESUME_ALEX.encode("utf-8")), "application/pdf")),
        ("files", ("lucas_silva.docx", io.BytesIO(RESUME_LUCAS.encode("utf-8")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
    ]
    upload_resp = client.post(f"/jobs/{job_id}/resumes", files=files)
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["total_uploaded"] == 2
    assert upload_data["total_successful"] == 2
    assert len(upload_data["files"]) == 2

    alex_cand_id = upload_data["files"][0]["candidate_id"]
    lucas_cand_id = upload_data["files"][1]["candidate_id"]
    assert alex_cand_id is not None
    assert lucas_cand_id is not None

    # 3. Trigger Candidate Matching
    match_resp = client.post(f"/jobs/{job_id}/match")
    assert match_resp.status_code == 200
    match_data = match_resp.json()
    assert match_data["total_matched"] == 2
    assert len(match_data["rankings"]) == 2

    # Verify Alex Mercer ranks higher than Lucas Silva
    first_rank = match_data["rankings"][0]
    second_rank = match_data["rankings"][1]
    assert first_rank["candidate_id"] == alex_cand_id
    assert first_rank["overall_score"] > second_rank["overall_score"]

    # 4. Fetch Rankings Leaderboard
    rankings_resp = client.get(f"/jobs/{job_id}/rankings")
    assert rankings_resp.status_code == 200
    leaderboard = rankings_resp.json()
    assert len(leaderboard) == 2
    assert leaderboard[0]["candidate_id"] == alex_cand_id
    assert "Python" in leaderboard[0]["matched_skills"]

    # 5. Fetch Detailed Candidate Analysis (Module 5)
    cand_resp = client.get(f"/candidates/{alex_cand_id}")
    assert cand_resp.status_code == 200
    cand_detail = cand_resp.json()
    assert cand_detail["name"] == "Alex Mercer"
    assert cand_detail["match_analysis"] is not None
    assert cand_detail["match_analysis"]["overall_score"] >= 75.0
    assert len(cand_detail["match_analysis"]["reasons"]) >= 3


def test_parse_job_preview():
    """Preview parsing returns extracted criteria without requiring a saved job."""
    response = client.post("/api/v1/jobs/parse", json={"raw_text": SAMPLE_JD})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Python / Machine Learning Engineer"
    assert "Python" in data["required_skills"]
    assert "AWS" in data["preferred_skills"]
    assert data["raw_text"] == SAMPLE_JD


def test_file_validation_rejections():
    """Verify that unsupported file types are rejected gracefully with informative reports."""
    # Create Job
    job_resp = client.post("/jobs/", json={"title": "Test Role", "raw_text": SAMPLE_JD})
    job_id = job_resp.json()["id"]

    # Upload invalid file (.exe / .zip)
    files = [
        ("files", ("malicious.exe", io.BytesIO(b"binary data"), "application/octet-stream")),
    ]
    upload_resp = client.post(f"/jobs/{job_id}/resumes", files=files)
    assert upload_resp.status_code == 201
    data = upload_resp.json()
    assert data["total_successful"] == 0
    assert data["total_failed"] == 1
    assert "Unsupported file type" in data["files"][0]["error"]
