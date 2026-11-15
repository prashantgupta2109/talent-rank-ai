"""Explainability service generating deterministic, plain-English justification points for match scores."""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.match import MatchResult


def generate_match_reasons(result: "MatchResult") -> List[str]:
    """Convert candidate match metrics into 3 to 5 human-readable explanation bullets.

    Deterministic template-based explanation (strictly zero LLM calls).

    Args:
        result: MatchResult containing overall and component scores.

    Returns:
        List of 3 to 5 clear, concise sentences explaining the percentage score.
    """
    reasons: List[str] = []

    # 1. Skill Match Explanation
    total_matched = len(result.matched_skills) + len(result.semantically_matched_skills)
    total_skills = total_matched + len(result.missing_skills)

    if total_skills > 0:
        skill_pct = int((total_matched / total_skills) * 100)
        skill_sentence = f"Matched {total_matched} of {total_skills} identified skills ({skill_pct}% overlap)"
        if result.missing_skills:
            missing_sample = ", ".join(result.missing_skills[:3])
            skill_sentence += f"; missing {missing_sample}."
        else:
            skill_sentence += "; covers all mandatory technical requirements."
        reasons.append(skill_sentence)

    # 2. Semantic Skill Nuance (if semantic matches occurred)
    if result.semantically_matched_skills:
        top_sem = result.semantically_matched_skills[0]
        reasons.append(
            f"Demonstrated semantic equivalence: candidate's '{top_sem.resume_skill}' satisfied JD requirement '{top_sem.jd_skill}' ({int(top_sem.similarity * 100)}% similarity)."
        )

    # 3. Experience Duration Analysis
    exp = result.experience_comparison
    if exp.required_years > 0:
        if exp.difference >= 0:
            diff_str = f"+{exp.difference:.1f}" if exp.difference > 0 else "exact match"
            reasons.append(
                f"Has {exp.candidate_years:.1f} years of relevant experience vs. {exp.required_years:.1f} required ({diff_str} years)."
            )
        else:
            reasons.append(
                f"Has {exp.candidate_years:.1f} years of experience, falling short of the {exp.required_years:.1f} years required ({exp.difference:.1f} years deficit)."
            )
    else:
        reasons.append(f"Possesses {exp.candidate_years:.1f} years of cumulative professional experience.")

    # 4. Semantic Alignment
    if result.semantic_score >= 80.0:
        reasons.append(
            f"High semantic alignment ({result.semantic_score:.1f}%) across core responsibilities and technical workflows."
        )
    elif result.semantic_score >= 60.0:
        reasons.append(
            f"Moderate semantic alignment ({result.semantic_score:.1f}%) with several relevant project responsibilities."
        )
    else:
        reasons.append(
            f"Low semantic relevance ({result.semantic_score:.1f}%) between past work history and target job duties."
        )

    # 5. Education & Overall Verdict
    edu = result.education_comparison
    if edu.candidate_degrees:
        deg_str = ", ".join(edu.candidate_degrees)
        if edu.meets_requirement:
            reasons.append(f"Satisfies educational criteria ({deg_str}).")
        else:
            reasons.append(f"Holds {deg_str}, partially meeting preferred qualifications.")

    return reasons[:5]
