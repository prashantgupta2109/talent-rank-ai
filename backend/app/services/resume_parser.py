"""Resume document parsing service supporting PDF, DOCX, and text formats with interval-merged experience."""

import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import pdfplumber
import docx
from app.schemas.resume import ParsedResume, EducationEntry, WorkExperienceEntry
from app.services.skill_extractor import extract_skills_from_text

# Regular expressions for contact information
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(
    r"(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?"
)
FALLBACK_PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

# Section header regex patterns
SECTION_PATTERNS = {
    "experience": re.compile(
        r"^(?:(?:work\s+experience|professional\s+experience|employment\s+history|"
        r"work\s+history|experience|career\s+history))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:(?:education|academic\s+background|academic\s+qualifications|degrees?))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:(?:technical\s+skills|skills|core\s+competencies|technologies|tools\s+&\s+technologies))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:(?:projects|personal\s+projects|key\s+projects))[\s:*-]*$",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:(?:summary|professional\s+summary|profile|about\s+me))[\s:*-]*$",
        re.IGNORECASE,
    ),
}

# Month names mapping to float year fraction
MONTHS_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Regex for date ranges (e.g. 'Jan 2020 – Present', '03/2018 - 11/2021', '2019 - 2023')
DATE_RANGE_REGEX = re.compile(
    r"\b((?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?\d{4}|\d{1,2}/\d{4}|\d{1,2}/\d{2})"
    r"\s*(?:–|—|-|to)\s*"
    r"((?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?\d{4}|\d{1,2}/\d{4}|\d{1,2}/\d{2}|present|current|now|till\s+date)\b",
    re.IGNORECASE,
)


def _extract_text_from_pdf(file_bytes: bytes, warnings: List[str]) -> str:
    """Extract full textual content from PDF file bytes using pdfplumber."""
    extracted_pages: List[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text(layout=True) or page.extract_text() or ""
                extracted_pages.append(page_text)
                # Also extract any table content
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        row_text = " | ".join([cell for cell in row if cell])
                        if row_text:
                            extracted_pages.append(row_text)
    except Exception as e:
        warnings.append(f"pdfplumber encountered error reading PDF: {str(e)}")

    return "\n".join(extracted_pages)


def _extract_text_from_docx(file_bytes: bytes, warnings: List[str]) -> str:
    """Extract full textual content including tables from DOCX file bytes."""
    lines: List[str] = []
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        # Extract normal paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)

        # Extract table contents (tables frequently hold header/skills data)
        for table in doc.tables:
            for row in table.rows:
                cell_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cell_texts:
                    lines.append(" | ".join(cell_texts))
    except Exception as e:
        warnings.append(f"python-docx encountered error reading DOCX: {str(e)}")

    return "\n".join(lines)


def _parse_date_string(date_str: str) -> Optional[float]:
    """Convert flexible date strings (e.g. 'Jan 2020', '03/2019', '2018', 'Present') to decimal year."""
    clean = date_str.strip().lower()
    if clean in ("present", "current", "now", "till date"):
        now = datetime.now()
        return now.year + (now.month / 12.0)

    # Check 'Month Year' e.g. 'Jan 2020' or 'January 2020'
    m_match = re.match(r"^([a-z]+)\.?\s+(\d{4})$", clean)
    if m_match:
        m_name, year_s = m_match.groups()
        month = MONTHS_MAP.get(m_name[:3], 6)
        return int(year_s) + (month / 12.0)

    # Check 'MM/YYYY' or 'M/YYYY'
    slash_match = re.match(r"^(\d{1,2})/(\d{4})$", clean)
    if slash_match:
        m_val, year_s = slash_match.groups()
        m_int = max(1, min(12, int(m_val)))
        return int(year_s) + (m_int / 12.0)

    # Check simple 4-digit year '2020'
    y_match = re.match(r"^(\d{4})$", clean)
    if y_match:
        return float(y_match.group(1)) + 0.5  # Mid-year estimate

    return None


def _calculate_merged_experience(intervals: List[Tuple[float, float]]) -> float:
    """Merge overlapping time intervals and compute total professional experience in years."""
    if not intervals:
        return 0.0

    # Filter invalid intervals (start > end or outside realistic range 1980-2035)
    valid_intervals = [
        (s, e) for s, e in intervals
        if 1970 <= s <= 2040 and 1970 <= e <= 2040 and e >= s
    ]
    if not valid_intervals:
        return 0.0

    # Sort intervals by start time ascending
    sorted_intervals = sorted(valid_intervals, key=lambda x: (x[0], x[1]))

    merged: List[Tuple[float, float]] = []
    curr_start, curr_end = sorted_intervals[0]

    for next_start, next_end in sorted_intervals[1:]:
        if next_start <= curr_end:
            # Overlapping or adjacent interval, extend the end
            curr_end = max(curr_end, next_end)
        else:
            merged.append((curr_start, curr_end))
            curr_start, curr_end = next_start, next_end

    merged.append((curr_start, curr_end))

    total_years = sum(end - start for start, end in merged)
    return round(total_years, 1)


def _segment_resume_sections(lines: List[str]) -> Dict[str, List[str]]:
    """Partition resume lines into structured sections based on recognized headers."""
    sections: Dict[str, List[str]] = {
        "header": [],
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "summary": [],
        "other": [],
    }

    current_section = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line matches a known section header
        header_candidate = re.sub(r"[:#*\-_]+$", "", stripped).strip()
        matched = False
        for sec_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(header_candidate):
                current_section = sec_name
                matched = True
                break

        if not matched:
            sections[current_section].append(stripped)

    return sections


def _extract_name(lines: List[str], header_lines: List[str]) -> str:
    """Identify candidate name from top lines, ignoring contact labels."""
    candidates = header_lines if header_lines else lines[:8]
    invalid_keywords = {
        "resume", "curriculum", "vitae", "cv", "profile", "contact", "email",
        "phone", "developer", "engineer", "scientist", "experience", "education",
        "page", "github", "linkedin", "portfolio", "address", "summary"
    }

    for line in candidates:
        cleaned = line.strip()
        if not cleaned:
            continue
        # Skip if contains email or phone
        if EMAIL_REGEX.search(cleaned) or FALLBACK_PHONE_REGEX.search(cleaned):
            continue

        words = cleaned.split()
        if 2 <= len(words) <= 4:
            lower_words = {w.lower() for w in words}
            if not (lower_words & invalid_keywords):
                # Ensure contains only alphabetic characters
                if all(re.match(r"^[A-Za-z.'-]+$", w) for w in words):
                    return cleaned

    return "Candidate"


def _extract_work_entries(
    exp_lines: List[str],
    full_text: str,
) -> Tuple[List[WorkExperienceEntry], List[Tuple[float, float]]]:
    """Extract individual work entries and collected date intervals."""
    entries: List[WorkExperienceEntry] = []
    intervals: List[Tuple[float, float]] = []

    # Search for all date ranges in experience section first, or full text
    target_lines = exp_lines if exp_lines else full_text.splitlines()

    for i, line in enumerate(target_lines):
        match = DATE_RANGE_REGEX.search(line)
        if match:
            start_str, end_str = match.groups()
            s_val = _parse_date_string(start_str)
            e_val = _parse_date_string(end_str)

            if s_val is not None and e_val is not None and e_val >= s_val:
                duration = round(e_val - s_val, 1)
                intervals.append((s_val, e_val))

                # Infer title or company from surrounding text
                title = "Software Engineer"
                company = None

                # Check before or after date in the same line or previous line
                line_without_date = DATE_RANGE_REGEX.sub("", line).strip(" -|•,")
                if len(line_without_date) > 3:
                    parts = [p.strip() for p in line_without_date.split("|") if p.strip()]
                    if len(parts) >= 2:
                        title, company = parts[0], parts[1]
                    else:
                        title = parts[0]
                elif i > 0:
                    prev_line = target_lines[i - 1].strip(" -|•,")
                    if len(prev_line) > 3 and not DATE_RANGE_REGEX.search(prev_line):
                        title = prev_line

                entries.append(
                    WorkExperienceEntry(
                        title=title[:80],
                        company=company[:80] if company else None,
                        start_date=start_str.strip(),
                        end_date=end_str.strip(),
                        duration_years=duration,
                        description=line.strip()[:200],
                    )
                )

    return entries, intervals


def _extract_education_entries(edu_lines: List[str], full_text: str) -> List[EducationEntry]:
    """Parse degrees, institutions, and graduation years from education section."""
    entries: List[EducationEntry] = []
    lines = edu_lines if edu_lines else full_text.splitlines()

    degree_pattern = re.compile(
        r"\b(bachelor(?:'s)?|master(?:'s)?|ph\.?d|b\.?s\.?|m\.?s\.?|b\.?tech|m\.?tech|b\.?e\.?|associate)\b",
        re.IGNORECASE,
    )
    year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")

    for line in lines:
        d_match = degree_pattern.search(line)
        if d_match:
            deg_term = d_match.group(0).title()
            y_match = year_pattern.search(line)
            grad_year = int(y_match.group(0)) if y_match else None

            # Check field of study
            field = None
            if re.search(r"\bcomputer\s+science\b", line, re.IGNORECASE):
                field = "Computer Science"
            elif re.search(r"\bdata\s+science\b", line, re.IGNORECASE):
                field = "Data Science"
            elif re.search(r"\bsoftware\s+engineering\b", line, re.IGNORECASE):
                field = "Software Engineering"
            elif re.search(r"\belectrical\b", line, re.IGNORECASE):
                field = "Electrical Engineering"
            elif re.search(r"\bmathematics|statistics\b", line, re.IGNORECASE):
                field = "Mathematics & Statistics"

            entries.append(
                EducationEntry(
                    degree=deg_term,
                    institution=line[:100],
                    field_of_study=field,
                    graduation_year=grad_year,
                )
            )

    return entries


def parse_resume_file(
    file_bytes: bytes,
    filename: str = "",
) -> ParsedResume:
    """Extract raw text from PDF or DOCX file, parse candidate profile, and compute merged experience.

    Args:
        file_bytes: Raw binary bytes of uploaded resume.
        filename: Original file name used to determine parser format.

    Returns:
        Structured ParsedResume model with non-fatal warnings if any issues occur.
    """
    warnings: List[str] = []
    raw_text = ""
    lower_fn = filename.lower()

    if not file_bytes:
        warnings.append("Received empty file bytes.")
        return ParsedResume(warnings=warnings, filename=filename)

    # 1. Format-specific extraction
    if lower_fn.endswith(".pdf"):
        raw_text = _extract_text_from_pdf(file_bytes, warnings)
    elif lower_fn.endswith((".docx", ".doc")):
        raw_text = _extract_text_from_docx(file_bytes, warnings)
    else:
        # Fallback to UTF-8 text decoding
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = file_bytes.decode("latin-1")
            except Exception as e:
                warnings.append(f"Could not decode text file: {str(e)}")

    if not raw_text.strip():
        warnings.append(f"No extractable text found in file '{filename}'. Document may be scanned or empty.")
        return ParsedResume(raw_text=raw_text, warnings=warnings, filename=filename)

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    sections = _segment_resume_sections(lines)

    # 2. Extract contact details
    email_match = EMAIL_REGEX.search(raw_text)
    email = email_match.group(0) if email_match else None

    phone_match = PHONE_REGEX.search(raw_text) or FALLBACK_PHONE_REGEX.search(raw_text)
    phone = phone_match.group(0).strip() if phone_match else None

    # 3. Extract candidate name
    candidate_name = _extract_name(lines, sections["header"])

    # 4. Extract skills using canonical taxonomy extractor
    skills = extract_skills_from_text(raw_text)

    # 5. Extract work experience and merge overlapping date intervals
    work_entries, intervals = _extract_work_entries(sections["experience"], raw_text)
    total_years = _calculate_merged_experience(intervals)

    # 6. Extract education qualifications
    education_entries = _extract_education_entries(sections["education"], raw_text)

    return ParsedResume(
        candidate_name=candidate_name,
        email=email,
        phone=phone,
        skills=skills,
        total_years_experience=total_years,
        work_experience=work_entries,
        education=education_entries,
        raw_text=raw_text,
        warnings=warnings,
        filename=filename,
    )
