"""Skill extraction service using taxonomy and spaCy PhraseMatcher."""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import spacy
from spacy.matcher import PhraseMatcher

# Cache for loaded matcher and taxonomy
_SPACY_NLP = None
_PHRASE_MATCHER = None
_ALIAS_TO_CANONICAL: Dict[str, str] = {}
_CANONICAL_SKILLS: Set[str] = set()


def _get_taxonomy_path() -> Path:
    """Return absolute path to skills.json taxonomy."""
    return Path(__file__).resolve().parent.parent / "data" / "skills.json"


def _initialize_extractor() -> None:
    """Initialize spaCy English pipeline and build PhraseMatcher from skills taxonomy."""
    global _SPACY_NLP, _PHRASE_MATCHER, _ALIAS_TO_CANONICAL, _CANONICAL_SKILLS

    if _PHRASE_MATCHER is not None:
        return

    # Use lightweight blank English model for fast, deterministic tokenization
    try:
        _SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception:
        _SPACY_NLP = spacy.blank("en")

    _PHRASE_MATCHER = PhraseMatcher(_SPACY_NLP.vocab, attr="LOWER")
    _ALIAS_TO_CANONICAL = {}
    _CANONICAL_SKILLS = set()

    taxonomy_file = _get_taxonomy_path()
    if not taxonomy_file.exists():
        return

    with open(taxonomy_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", {})
    patterns_by_canonical: Dict[str, List] = {}

    for cat_name, skill_entries in categories.items():
        for entry in skill_entries:
            canonical = entry["name"]
            _CANONICAL_SKILLS.add(canonical)
            aliases = entry.get("aliases", [])

            # Add canonical itself as an alias
            all_terms = set(aliases) | {canonical}

            for term in all_terms:
                term_clean = term.strip()
                if not term_clean:
                    continue
                _ALIAS_TO_CANONICAL[term_clean.lower()] = canonical

                doc = _SPACY_NLP.make_doc(term_clean)
                if canonical not in patterns_by_canonical:
                    patterns_by_canonical[canonical] = []
                patterns_by_canonical[canonical].append(doc)

    for canonical, docs in patterns_by_canonical.items():
        _PHRASE_MATCHER.add(canonical, docs)


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known technical and soft skills from arbitrary text.

    Args:
        text: Input string (job description section, resume chunk, etc.)

    Returns:
        List of unique canonical skill names found in the text.
    """
    if not text or not text.strip():
        return []

    _initialize_extractor()
    if _PHRASE_MATCHER is None or _SPACY_NLP is None:
        return []

    doc = _SPACY_NLP(text)
    matches = _PHRASE_MATCHER(doc)

    found_skills: List[str] = []
    seen: Set[str] = set()

    # Sort matches by span length descending to give precedence to longer phrases
    # (e.g. 'Apache Spark' over 'Spark', 'Ruby on Rails' over 'Ruby')
    matches = sorted(matches, key=lambda m: (m[2] - m[1]), reverse=True)

    matched_token_indices: Set[int] = set()

    for match_id, start, end in matches:
        token_range = set(range(start, end))
        # Prevent substring token overlap (e.g. matching 'C' inside 'C++' or 'Spring' inside 'Spring Boot')
        if token_range & matched_token_indices:
            continue

        canonical_name = _SPACY_NLP.vocab.strings[match_id]
        matched_token_indices.update(token_range)

        if canonical_name not in seen:
            seen.add(canonical_name)
            found_skills.append(canonical_name)

    return found_skills


def get_all_canonical_skills() -> Set[str]:
    """Return all canonical skill names present in the taxonomy."""
    _initialize_extractor()
    return set(_CANONICAL_SKILLS)


def normalize_skill(term: str) -> str:
    """Normalize any alias or variation to its canonical skill name if recognized."""
    _initialize_extractor()
    return _ALIAS_TO_CANONICAL.get(term.strip().lower(), term.strip())
