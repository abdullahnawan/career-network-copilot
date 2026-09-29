from app.models import Contact, StudentProfile


def words(value: str | None) -> set[str]:
    return {word.casefold() for word in (value or "").replace(",", " ").split() if word}


def overlap_score(targets: set[str], actual: str | None) -> float:
    if not targets or not actual:
        return 0.0
    return 100.0 if targets & words(actual) else 0.0


def calculate_match(
    profile: StudentProfile, contact: Contact
) -> tuple[float, dict[str, float], list[str]]:
    """Score exact normalized token overlap; every component is binary and explainable."""
    goals = profile.career_goals
    target_roles = set().union(*(words(goal.role) for goal in goals))
    target_industries = set().union(*(words(goal.industry) for goal in goals))
    target_locations = set().union(*(words(goal.location) for goal in goals))
    target_schools = words(profile.school)
    student_skills = set().union(*(words(skill.skill.name) for skill in profile.skills))

    breakdown = {
        "role": overlap_score(target_roles, contact.current_role),
        "industry": overlap_score(target_industries, contact.industry),
        "location": overlap_score(target_locations, contact.location),
        "school": overlap_score(target_schools, contact.school),
        "skills": overlap_score(student_skills, contact.skills_summary),
    }
    weights = {"role": 0.30, "industry": 0.20, "location": 0.15, "school": 0.15, "skills": 0.20}
    total = round(sum(breakdown[key] * weight for key, weight in weights.items()), 2)
    reasons = []
    labels = {
        "role": "target role",
        "industry": "target industry",
        "location": "preferred location",
        "school": "school",
        "skills": "skills",
    }
    for key, score in breakdown.items():
        if score:
            reasons.append(f"Matches your {labels[key]}.")
    if not reasons:
        reasons.append("No exact overlap was found in the available profile fields.")
    return total, breakdown, reasons
