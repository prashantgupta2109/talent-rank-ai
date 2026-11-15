"""Unit tests for Job Description parser using 3 realistic sample JDs."""

import pytest
from app.services.jd_parser import parse_job_description

# Sample 1: Senior Full-Stack Engineer
SAMPLE_JD_FULLSTACK = """
Job Title: Senior Full-Stack Python Developer

About Us:
We are building the next generation AI analytics platform.

Responsibilities:
- Design and implement scalable backend microservices using FastAPI and PostgreSQL.
- Build modern, interactive user interfaces with React and Tailwind CSS.
- Collaborate with product designers and ML engineers to deploy data dashboards.
- Write unit tests and maintain high code quality standards.

Requirements:
- 5+ years of experience in full-stack software development.
- Strong proficiency in Python, JavaScript, and TypeScript.
- Hands-on experience with FastAPI or Django.
- Solid experience with PostgreSQL database modeling and SQL queries.
- Bachelor's degree in Computer Science or related field.

Nice to Have:
- Experience with Docker, Kubernetes, and AWS deployment.
- Familiarity with Redis caching and GraphQL.
- Knowledge of Machine Learning concepts.
"""

# Sample 2: Machine Learning Engineer
SAMPLE_JD_ML = """
Role: Machine Learning Engineer - NLP / LLM

What You Will Do:
- Develop state-of-the-art Natural Language Processing models using PyTorch and Hugging Face.
- Build Retrieval-Augmented Generation (RAG) pipelines using LangChain and vector databases like ChromaDB.
- Optimize and fine-tune Large Language Models for production inference.
- Work closely with data engineers to build robust ETL pipelines in Apache Airflow.

Required Qualifications:
- 3 to 5 years of experience in Machine Learning and Data Science.
- Deep expertise in Python, PyTorch, and scikit-learn.
- Strong practical experience with spaCy, Transformers, and Sentence Transformers.
- Master's degree or Ph.D. in Computer Science, Data Science, or Mathematics.

Bonus Qualifications:
- Experience with MLflow and Weights & Biases for experiment tracking.
- Familiarity with FastAPI, Docker, and ONNX Runtime optimization.
"""

# Sample 3: Cloud & DevOps Engineer
SAMPLE_JD_DEVOPS = """
Position: Senior Cloud DevOps Engineer

The Role:
Maintain 99.99% availability of cloud infrastructure and automate release engineering.

Key Responsibilities:
- Manage multi-cluster Kubernetes environments on AWS (EKS).
- Develop Infrastructure as Code using Terraform and Ansible.
- Build reliable CI/CD pipelines using GitHub Actions and Jenkins.
- Monitor system health, logs, and metrics using Prometheus and Grafana.

Minimum Qualifications:
- At least 4 years of experience in DevOps, Cloud Engineering, or SRE roles.
- Deep understanding of AWS, Linux administration, and Bash scripting.
- Production experience with Docker and Kubernetes (k8s).
- Proven track record with Terraform and CI/CD automation.
- Bachelor's degree in Information Technology or equivalent practical experience.

Preferred Skills:
- Experience with Python or Go for infrastructure automation.
- Familiarity with ArgoCD, Helm charts, and Datadog.
"""


def test_fullstack_jd_parsing():
    """Verify parsing of Full-Stack Developer JD."""
    parsed = parse_job_description(SAMPLE_JD_FULLSTACK)

    assert "Senior Full-Stack Python Developer" in parsed.title
    assert parsed.min_years_experience == 5.0
    assert len(parsed.responsibilities) >= 3

    # Required skills verification
    req_skills = set(parsed.required_skills)
    assert "Python" in req_skills
    assert "JavaScript" in req_skills
    assert "TypeScript" in req_skills
    assert "FastAPI" in req_skills or "Django" in req_skills
    assert "PostgreSQL" in req_skills

    # Preferred skills verification
    pref_skills = set(parsed.preferred_skills)
    assert "Docker" in pref_skills
    assert "Kubernetes" in pref_skills
    assert "AWS" in pref_skills
    assert "Redis" in pref_skills

    # Ensure no overlap between required and preferred
    assert req_skills.isdisjoint(pref_skills)

    # Education verification
    edu_text = " ".join(parsed.education_requirements).lower()
    assert "bachelor" in edu_text
    assert "computer science" in edu_text


def test_ml_engineer_jd_parsing():
    """Verify parsing of Machine Learning Engineer JD."""
    parsed = parse_job_description(SAMPLE_JD_ML)

    assert "Machine Learning Engineer" in parsed.title
    assert parsed.min_years_experience == 3.0  # From '3 to 5 years'
    assert len(parsed.responsibilities) >= 3

    req_skills = set(parsed.required_skills)
    assert "Python" in req_skills
    assert "PyTorch" in req_skills
    assert "scikit-learn" in req_skills
    assert "Natural Language Processing" in req_skills or "Machine Learning" in req_skills

    pref_skills = set(parsed.preferred_skills)
    assert "MLflow" in pref_skills
    assert "Docker" in pref_skills or "FastAPI" in pref_skills

    edu_text = " ".join(parsed.education_requirements).lower()
    assert "master" in edu_text or "ph.d" in edu_text or "doctorate" in edu_text


def test_devops_engineer_jd_parsing():
    """Verify parsing of Cloud DevOps Engineer JD."""
    parsed = parse_job_description(SAMPLE_JD_DEVOPS)

    assert "Senior Cloud DevOps Engineer" in parsed.title
    assert parsed.min_years_experience == 4.0  # From 'At least 4 years'
    assert len(parsed.responsibilities) >= 3

    req_skills = set(parsed.required_skills)
    assert "AWS" in req_skills
    assert "Kubernetes" in req_skills
    assert "Docker" in req_skills
    assert "Terraform" in req_skills
    assert "Linux" in req_skills
    assert "CI/CD" in req_skills

    pref_skills = set(parsed.preferred_skills)
    assert "Go" in pref_skills or "Python" in pref_skills or "Helm" in pref_skills

    edu_text = " ".join(parsed.education_requirements).lower()
    assert "bachelor" in edu_text or "information technology" in edu_text


def test_empty_and_minimal_jd():
    """Verify safe fallback for empty and unstructured text."""
    empty_parsed = parse_job_description("")
    assert empty_parsed.title == "Software Engineer"
    assert empty_parsed.min_years_experience == 0.0
    assert empty_parsed.required_skills == []

    minimal_text = "Hiring a Java Developer with 2 years of experience in Spring Boot and SQL."
    minimal_parsed = parse_job_description(minimal_text)
    assert minimal_parsed.min_years_experience == 2.0
    assert "Java" in minimal_parsed.required_skills
    assert "Spring Boot" in minimal_parsed.required_skills
    assert "SQL" in minimal_parsed.required_skills
