from app.matching import calculate_match
from app.models import Contact, StudentProfile


def generate_suggestion(
    profile: StudentProfile,
    contact: Contact,
    purpose: str,
    channel: str,
    tone: str,
) -> tuple[str | None, str, list[str]]:
    """Build an editable, deterministic message from stored facts only."""
    _, _, match_reasons = calculate_match(profile, contact)
    facts: list[str] = []
    if contact.current_role:
        facts.append(f"Contact role: {contact.current_role}")
    if contact.company:
        facts.append(f"Contact company: {contact.company}")
    if contact.industry:
        facts.append(f"Contact industry: {contact.industry}")
    if profile.school:
        facts.append(f"Student school: {profile.school}")
    if profile.program:
        facts.append(f"Student program: {profile.program}")
    facts.extend(match_reasons)

    greeting = "Hi" if tone != "professional" else "Hello"
    name = contact.full_name.split()[0]
    goal = profile.career_goals[0].role if profile.career_goals else "career growth"
    purpose_text = {
        "informational_interview": "your career path",
        "career_advice": "career advice",
        "project_collaboration": "a possible project collaboration",
        "internship_question": "your perspective on internships",
        "general_networking": "your experience",
    }[purpose]
    message = f"{greeting} {name},\n\nI'm {profile.full_name}, a student interested in {goal}."
    if contact.current_role:
        message += f" I see that you work as {contact.current_role}"
    if contact.company:
        message += f" at {contact.company}"
    message += f". Would you be open to sharing {purpose_text}?"
    if tone != "concise" and profile.school:
        message += f" I'm studying at {profile.school}."
    message += f"\n\nBest,\n{profile.full_name}"
    subject = (
        f"Question about {contact.current_role or 'your experience'}"
        if channel == "email"
        else None
    )
    return subject, message, facts
