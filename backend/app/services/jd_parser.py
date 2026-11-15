"""Job Description parsing and entity extraction service using deterministic NLP and regex."""

import re
from typing import Dict, List, Optional, Tuple
from app.schemas.job import ParsedJobDescription
from app.services.skill_extractor import extract_skills_from_text

# Regex patterns for section headers
HEADER_PATTERNS = {
    "preferred": re.compile(
        r"^(?:(?:nice\s+to\s+have|preferred\s+qualifications?|preferred\s+skills?|"
        r"bonus\s+points?|bonus\s+qualifications?|desired\s+skills?|good\s+to\s+have|"
        r"what\s+gives\s+you\s+an\s+edge|optional\s+skills?))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "required": re.compile(
        r"^(?:(?:requirements?|required\s+qualifications?|minimum\s+qualifications?|"
        r"basic\s+qualifications?|must\s+haves?|what\s+you(?:'ll|\s+will)\s+need|"
        r"qualifications?|technical\s+requirements?|skills\s+required))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "responsibilities": re.compile(
        r"^(?:(?:responsibilities|key\s+responsibilities|job\s+responsibilities|"
        r"what\s+you(?:'ll|\s+will)\s+do|duties|what\s+you\s+bring|the\s+role|role\s+overview))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:(?:education|educational\s+requirements?|degrees?))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "about": re.compile(
        r"^(?:(?:about\s+us|company\s+overview|who\s+we\s+are|about\s+the\s+team))[\s:*-]*$",
        re.IGNORECASE,
    ),
}

# Regex for years of experience (e.g. '3+ years', '2-4 years', 'at least 5 years')
EXP_PATTERNS = [
    re.compile(
        r"(?:at\s+least|minimum|min\.?)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant|hands-on|professional|work))?\s+experience",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant|hands-on|professional|work))?\s+experience",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\+\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
]

# Patterns for education qualification
EDU_PATTERNS = [
    re.compile(r"\b(?:ph\.?d|doctorate|doctoral\s+degree)\b", re.IGNORECASE),
    re.compile(r"\b(?:master(?:'s)?\s+degree|m\.?s\.?|m\.?tech|m\.?e\.?|mba)\b", re.IGNORECASE),
    re.compile(r"\b(?:bachelor(?:'s)?\s+degree|b\.?s\.?|b\.?tech|b\.?e\.?|b\.?a\.?|undergraduate\s+degree)\b", re.IGNORECASE),
    re.compile(r"\b(?:computer\s+science|software\s+engineering|information\s+technology|data\s+science|electrical\s+engineering|mathematics|statistics)\b", re.IGNORECASE),
]


def _extract_job_title(lines: List[str]) -> str:
    """Identify job title from top lines or explicit title labels."""
    for line in lines[:10]:
        cleaned = line.strip()
        if not cleaned:
            continue

        # Check explicit label
        match = re.match(r"^(?:job\s+title|title|role|position)\s*[:\-]\s*(.+)$", cleaned, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Check if first non-empty line looks like a title (short, no bullet, no colon header)
        if len(cleaned) < 70 and not cleaned.endswith(":") and not cleaned.startswith(("*", "-", "•", "1.", "2.")):
            # Avoid generic company names or greetings
            if not re.search(r"\b(welcome|about us|hiring|overview)\b", cleaned, re.IGNORECASE):
                return cleaned

    return "Software Engineer"


def _split_into_sections(text: str) -> Dict[str, List[str]]:
    """Segment raw text into labeled logical sections based on headers."""
    lines = text.splitlines()
    sections: Dict[str, List[str]] = {
        "required": [],
        "preferred": [],
        "responsibilities": [],
        "education": [],
        "other": [],
    }

    current_section = "other"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_new_section = False
        # Check if line matches a known section header
        for section_key, pattern in HEADER_PATTERNS.items():
            # Match directly or header ending with colon
            header_candidate = re.sub(r"[:#*\-_]+$", "", stripped).strip()
            if pattern.match(header_candidate):
                current_section = section_key if section_key in sections else "other"
                matched_new_section = True
                break

        if not matched_new_section:
            sections[current_section].append(stripped)

    return sections


def _extract_min_experience(text: str) -> float:
    """Detect minimum required experience in years using regex patterns."""
    min_exp: Optional[float] = None

    for pattern in EXP_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            try:
                # If range '2-4 years', take lower bound 2
                val = float(groups[0])
                if 0.5 <= val <= 25.0:  # Sensible range for years of experience
                    if min_exp is None or val < min_exp:
                        min_exp = val
            except (ValueError, IndexError):
                continue

    return min_exp if min_exp is not None else 0.0


def _extract_education(text: str) -> List[str]:
    """Extract education degree mentions and STEM specializations."""
    edu_mentions: List[str] = []
    seen = set()

    for pattern in EDU_PATTERNS:
        for match in pattern.finditer(text):
            term = match.group(0).strip().title()
            if term.lower() not in seen:
                seen.add(term.lower())
                edu_mentions.append(term)

    return edu_mentions


def _extract_responsibilities(sections: Dict[str, List[str]]) -> List[str]:
    """Extract list of duties/responsibilities from identified sections."""
    resp_lines = sections.get("responsibilities", [])
    bullets: List[str] = []

    for line in resp_lines:
        cleaned = re.sub(r"^[\s*•\-\d.)]+", "", line).strip()
        if len(cleaned) > 15:  # Filter out trivial fragments
            bullets.append(cleaned)

    return bullets


def parse_job_description(text: str) -> ParsedJobDescription:
    """Parse raw Job Description text into structured requirements, skills, and qualifications.

    Args:
        text: Raw text of the job posting.

    Returns:
        ParsedJobDescription instance with extracted attributes.
    """
    if not text or not text.strip():
        return ParsedJobDescription(raw_text=text)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = _extract_job_title(lines)
    sections = _split_into_sections(text)

    # 1. Extract required skills
    req_text = " \n ".join(sections["required"])
    required_skills = extract_skills_from_text(req_text)

    # 2. Extract preferred / nice-to-have skills
    pref_text = " \n ".join(sections["preferred"])
    preferred_skills = extract_skills_from_text(pref_text)

    # If no required section was explicitly flagged, check general/other text
    if not required_skills and not preferred_skills:
        all_skills = extract_skills_from_text(text)
        required_skills = all_skills
    elif not required_skills and sections["other"]:
        other_skills = extract_skills_from_text(" \n ".join(sections["other"]))
        required_skills = [s for s in other_skills if s not in preferred_skills]

    # Deduplicate: if skill appears in both, required takes precedence
    req_set = set(required_skills)
    preferred_skills = [s for s in preferred_skills if s not in req_set]

    # 3. Experience requirements
    # Prefer experience mentioned in required section, then fallback to full text
    min_exp = _extract_min_experience(req_text)
    if min_exp == 0.0:
        min_exp = _extract_min_experience(text)

    # 4. Education requirements
    edu_text = " \n ".join(sections["education"] + sections["required"] + sections["other"])
    education_reqs = _extract_education(edu_text)

    # 5. Responsibilities
    responsibilities = _extract_responsibilities(sections)

    return ParsedJobDescription(
        title=title,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_years_experience=min_exp,
        education_requirements=education_reqs,
        responsibilities=responsibilities,
        raw_text=text,
    )
