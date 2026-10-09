import csv
import io
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import CurrentUser
from app.db import get_db
from app.matching import calculate_match
from app.models import (
    CareerGoal,
    Contact,
    OutreachDraft,
    OutreachDraftStatus,
    Skill,
    StudentProfile,
    StudentSkill,
)
from app.outreach import generate_suggestion
from app.schemas import (
    CareerGoalCreate,
    CareerGoalResponse,
    CareerGoalUpdate,
    ContactCreate,
    ContactMatch,
    ContactPage,
    ContactResponse,
    ContactUpdate,
    CsvImportError,
    CsvImportSummary,
    OutreachActivitySummary,
    OutreachDraftCreate,
    OutreachDraftPage,
    OutreachDraftResponse,
    OutreachDraftUpdate,
    OutreachSuggestion,
    SkillInput,
    SkillListRequest,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from app.schemas import (
    OutreachDraftStatus as OutreachDraftStatusSchema,
)

router = APIRouter(prefix="/student-profiles", tags=["student profiles"])
contacts_router = APIRouter(prefix="/contacts", tags=["contacts"])
outreach_router = APIRouter(prefix="/outreach-drafts", tags=["outreach drafts"])

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 500
CONNECTION_NOTE_LIMIT = 300
CSV_REQUIRED_COLUMNS = {"full_name", "source_name"}
CSV_OPTIONAL_COLUMNS = {
    "current_role",
    "company",
    "industry",
    "location",
    "school",
    "skills_summary",
    "profile_url",
    "source_type",
    "notes",
}


def profile_query(profile_id: int, owner_id: int):
    return (
        select(StudentProfile)
        .where(StudentProfile.id == profile_id, StudentProfile.owner_id == owner_id)
        .options(
            selectinload(StudentProfile.career_goals),
            selectinload(StudentProfile.skills).selectinload(StudentSkill.skill),
        )
    )


def get_profile_or_404(db: Session, profile_id: int, owner_id: int) -> StudentProfile:
    profile = db.scalar(profile_query(profile_id, owner_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def get_current_profile_or_404(db: Session, owner_id: int) -> StudentProfile:
    profile = db.scalar(
        select(StudentProfile)
        .where(StudentProfile.owner_id == owner_id)
        .options(
            selectinload(StudentProfile.career_goals),
            selectinload(StudentProfile.skills).selectinload(StudentSkill.skill),
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


def add_skills(db: Session, profile: StudentProfile, skills: list[SkillInput]) -> None:
    for item in skills:
        skill = db.scalar(select(Skill).where(Skill.name == item.name))
        if skill is None:
            skill = Skill(name=item.name)
            db.add(skill)
            db.flush()
        profile.skills.append(StudentSkill(skill=skill, proficiency_level=item.proficiency_level))


@router.post("", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: StudentProfileCreate, user: CurrentUser, db: Session = Depends(get_db)):
    if db.scalar(select(StudentProfile.id).where(StudentProfile.owner_id == user.id)) is not None:
        raise HTTPException(
            status_code=409,
            detail="A student profile already exists for this account",
        )
    profile = StudentProfile(
        owner_id=user.id, **payload.model_dump(exclude={"career_goals", "skills"})
    )
    profile.career_goals = [CareerGoal(**goal.model_dump()) for goal in payload.career_goals]
    db.add(profile)
    db.flush()
    add_skills(db, profile, payload.skills)
    db.commit()
    return get_profile_or_404(db, profile.id, user.id)


@router.get("/me", response_model=StudentProfileResponse)
def get_current_profile(user: CurrentUser, db: Session = Depends(get_db)):
    return get_current_profile_or_404(db, user.id)


@router.get("/{profile_id}", response_model=StudentProfileResponse)
def get_profile(profile_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    return get_profile_or_404(db, profile_id, user.id)


@router.patch("/{profile_id}", response_model=StudentProfileResponse)
def update_profile(
    profile_id: int, payload: StudentProfileUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    profile = get_profile_or_404(db, profile_id, user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    return get_profile_or_404(db, profile_id, user.id)


@router.post("/{profile_id}/career-goals", response_model=CareerGoalResponse, status_code=201)
def create_goal(
    profile_id: int, payload: CareerGoalCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    profile = get_profile_or_404(db, profile_id, user.id)
    goal = CareerGoal(student_profile_id=profile.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{profile_id}/career-goals/{goal_id}", response_model=CareerGoalResponse)
def update_goal(
    profile_id: int,
    goal_id: int,
    payload: CareerGoalUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    get_profile_or_404(db, profile_id, user.id)
    goal = db.scalar(
        select(CareerGoal).where(
            CareerGoal.id == goal_id, CareerGoal.student_profile_id == profile_id
        )
    )
    if goal is None:
        raise HTTPException(status_code=404, detail="Career goal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{profile_id}/career-goals/{goal_id}", status_code=204)
def delete_goal(profile_id: int, goal_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    get_profile_or_404(db, profile_id, user.id)
    goal = db.scalar(
        select(CareerGoal).where(
            CareerGoal.id == goal_id, CareerGoal.student_profile_id == profile_id
        )
    )
    if goal is None:
        raise HTTPException(status_code=404, detail="Career goal not found")
    db.delete(goal)
    db.commit()


@router.put("/{profile_id}/skills", response_model=StudentProfileResponse)
def replace_skills(
    profile_id: int, payload: SkillListRequest, user: CurrentUser, db: Session = Depends(get_db)
):
    profile = get_profile_or_404(db, profile_id, user.id)
    profile.skills.clear()
    db.flush()
    add_skills(db, profile, payload.skills)
    db.commit()
    return get_profile_or_404(db, profile_id, user.id)


@router.get("/{profile_id}/matches", response_model=list[ContactMatch])
def get_matches(profile_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, profile_id, user.id)
    contacts = db.scalars(
        select(Contact).where(Contact.owner_id == user.id).order_by(Contact.created_at.desc())
    ).all()
    matches = []
    for contact in contacts:
        total, breakdown, reasons = calculate_match(profile, contact)
        matches.append(
            ContactMatch(
                contact=contact,
                total_score=total,
                breakdown=breakdown,
                reasons=reasons,
            )
        )
    return sorted(matches, key=lambda item: (-item.total_score, item.contact.id))


def contact_or_404(db: Session, contact_id: int, owner_id: int) -> Contact:
    contact = db.scalar(
        select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@contacts_router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, user: CurrentUser, db: Session = Depends(get_db)):
    contact = Contact(owner_id=user.id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@contacts_router.get("", response_model=ContactPage)
def list_contacts(
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = None,
    company: str | None = None,
    industry: str | None = None,
    location: str | None = None,
    school: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    filters = []
    for field, value in (
        (Contact.current_role, role),
        (Contact.company, company),
        (Contact.industry, industry),
        (Contact.location, location),
        (Contact.school, school),
    ):
        if value:
            filters.append(field.ilike(f"%{value.strip()}%"))
    if q:
        term = f"%{q.strip()}%"
        filters.append(
            or_(
                Contact.full_name.ilike(term),
                Contact.current_role.ilike(term),
                Contact.company.ilike(term),
                Contact.industry.ilike(term),
                Contact.location.ilike(term),
                Contact.school.ilike(term),
                Contact.skills_summary.ilike(term),
                Contact.notes.ilike(term),
            )
        )
    query = (
        select(Contact)
        .where(Contact.owner_id == user.id, *filters)
        .order_by(Contact.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    contacts = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return ContactPage(items=contacts, page=page, page_size=page_size, total=total)


@contacts_router.post("/import-csv", response_model=CsvImportSummary)
async def import_contacts_csv(
    user: CurrentUser,
    file: Annotated[UploadFile, File(description="CSV with fictional or user-authorized contacts")],
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV file must be 5 MB or smaller")
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
    except (UnicodeDecodeError, csv.Error) as error:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {error}") from error
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must include a header row")
    headers = {header.strip() for header in reader.fieldnames if header}
    missing = CSV_REQUIRED_COLUMNS - headers
    unsupported = headers - CSV_REQUIRED_COLUMNS - CSV_OPTIONAL_COLUMNS
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported columns: {', '.join(sorted(unsupported))}",
        )

    errors: list[CsvImportError] = []
    created = 0
    for row_number, row in enumerate(reader, start=2):
        if row_number > MAX_CSV_ROWS + 1:
            errors.append(CsvImportError(row=row_number, message="Import limit is 500 rows"))
            break
        values = {key.strip(): (value or "").strip() for key, value in row.items() if key}
        formula_fields = [
            key for key, value in values.items() if value.startswith(("=", "+", "-", "@"))
        ]
        if formula_fields:
            errors.append(
                CsvImportError(
                    row=row_number,
                    message=f"Formula-like values are not allowed: {', '.join(formula_fields)}",
                )
            )
            continue
        if not values.get("full_name") or not values.get("source_name"):
            errors.append(
                CsvImportError(row=row_number, message="full_name and source_name are required")
            )
            continue
        source_type = values.get("source_type") or "csv"
        if source_type != "csv":
            errors.append(CsvImportError(row=row_number, message="source_type must be csv"))
            continue
        try:
            contact = ContactCreate(
                full_name=values["full_name"],
                current_role=values.get("current_role") or None,
                company=values.get("company") or None,
                industry=values.get("industry") or None,
                location=values.get("location") or None,
                school=values.get("school") or None,
                skills_summary=values.get("skills_summary") or None,
                profile_url=values.get("profile_url") or None,
                source_type="csv",
                source_name=values["source_name"],
                notes=values.get("notes") or None,
            )
        except ValueError as error:
            errors.append(CsvImportError(row=row_number, message=str(error)))
            continue
        db.add(Contact(owner_id=user.id, **contact.model_dump()))
        created += 1
    db.commit()
    return CsvImportSummary(created=created, errors=errors)


@contacts_router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    return contact_or_404(db, contact_id, user.id)


@contacts_router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int, payload: ContactUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    contact = contact_or_404(db, contact_id, user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@contacts_router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    contact = contact_or_404(db, contact_id, user.id)
    db.delete(contact)
    db.commit()


def draft_or_404(db: Session, draft_id: int, owner_id: int) -> OutreachDraft:
    draft = db.scalar(
        select(OutreachDraft).where(
            OutreachDraft.id == draft_id, OutreachDraft.owner_id == owner_id
        )
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="Outreach draft not found")
    return draft


def transition(draft: OutreachDraft, target: OutreachDraftStatus) -> None:
    current = OutreachDraftStatus(draft.status)
    allowed = {
        OutreachDraftStatus.DRAFT: {
            OutreachDraftStatus.APPROVED,
            OutreachDraftStatus.ARCHIVED,
        },
        OutreachDraftStatus.APPROVED: {
            OutreachDraftStatus.COPIED,
            OutreachDraftStatus.ARCHIVED,
        },
        OutreachDraftStatus.COPIED: {
            OutreachDraftStatus.SENT_MANUALLY,
            OutreachDraftStatus.ARCHIVED,
        },
        OutreachDraftStatus.SENT_MANUALLY: {
            OutreachDraftStatus.REPLIED,
            OutreachDraftStatus.ARCHIVED,
        },
        OutreachDraftStatus.REPLIED: {OutreachDraftStatus.ARCHIVED},
        OutreachDraftStatus.ARCHIVED: set(),
    }
    if target not in allowed[current]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition outreach draft from {current.value} to {target.value}",
        )
    draft.status = target.value
    timestamp_fields = {
        OutreachDraftStatus.COPIED: "copied_at",
        OutreachDraftStatus.SENT_MANUALLY: "sent_manually_at",
        OutreachDraftStatus.REPLIED: "replied_at",
    }
    timestamp_field = timestamp_fields.get(target)
    if timestamp_field is not None:
        setattr(draft, timestamp_field, datetime.now(timezone.utc))


@outreach_router.post("", response_model=OutreachDraftResponse, status_code=201)
def create_outreach_draft(
    payload: OutreachDraftCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    if (
        db.scalar(
            select(StudentProfile).where(
                StudentProfile.id == payload.student_profile_id, StudentProfile.owner_id == user.id
            )
        )
        is None
    ):
        raise HTTPException(status_code=404, detail="Student profile not found")
    if (
        db.scalar(
            select(Contact).where(Contact.id == payload.contact_id, Contact.owner_id == user.id)
        )
        is None
    ):
        raise HTTPException(status_code=404, detail="Contact not found")
    if (
        payload.channel == "linkedin_connection_note"
        and len(payload.message) > CONNECTION_NOTE_LIMIT
    ):
        raise HTTPException(
            status_code=422,
            detail="linkedin_connection_note messages must be 300 characters or fewer",
        )
    draft = OutreachDraft(owner_id=user.id, **payload.model_dump())
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@outreach_router.get("", response_model=OutreachDraftPage)
def list_outreach_drafts(
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: OutreachDraftStatusSchema | None = Query(default=None, alias="status"),
    purpose: str | None = None,
    channel: str | None = None,
    student_profile_id: int | None = Query(default=None, gt=0),
    contact_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = select(OutreachDraft).where(OutreachDraft.owner_id == user.id)
    if status_filter:
        query = query.where(OutreachDraft.status == status_filter.value)
    if student_profile_id:
        query = query.where(OutreachDraft.student_profile_id == student_profile_id)
    if contact_id:
        query = query.where(OutreachDraft.contact_id == contact_id)
    if purpose:
        query = query.where(OutreachDraft.purpose == purpose)
    if channel:
        query = query.where(OutreachDraft.channel == channel)
    query = query.order_by(OutreachDraft.created_at.desc(), OutreachDraft.id.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return OutreachDraftPage(items=items, page=page, page_size=page_size, total=total)


@outreach_router.get("/activity-summary", response_model=OutreachActivitySummary)
@outreach_router.get("/activity", response_model=OutreachActivitySummary, include_in_schema=False)
def outreach_activity_summary(
    user: CurrentUser,
    student_profile_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = (
        select(OutreachDraft.status, func.count())
        .where(OutreachDraft.owner_id == user.id)
        .group_by(OutreachDraft.status)
    )
    if student_profile_id:
        query = query.where(OutreachDraft.student_profile_id == student_profile_id)
    counts = {status.value: 0 for status in OutreachDraftStatus}
    total = 0
    for value, count in db.execute(query):
        counts[value] = count
        total += count
    return OutreachActivitySummary(total=total, by_status=counts)


@outreach_router.post("/suggest", response_model=OutreachSuggestion)
@outreach_router.post("/suggestion", response_model=OutreachSuggestion, include_in_schema=False)
def suggest_outreach(
    user: CurrentUser,
    student_profile_id: int = Query(gt=0),
    contact_id: int = Query(gt=0),
    purpose: str = Query(...),
    channel: str = Query(...),
    tone: str = Query(...),
    db: Session = Depends(get_db),
):
    profile = get_profile_or_404(db, student_profile_id, user.id)
    contact = contact_or_404(db, contact_id, user.id)
    allowed_purposes = {
        "informational_interview",
        "career_advice",
        "project_collaboration",
        "internship_question",
        "general_networking",
    }
    allowed_channels = {"linkedin_connection_note", "linkedin_message", "email", "other"}
    allowed_tones = {"professional", "warm", "concise"}
    if (
        purpose not in allowed_purposes
        or channel not in allowed_channels
        or tone not in allowed_tones
    ):
        raise HTTPException(status_code=422, detail="Invalid purpose, channel, or tone")
    subject, message, facts_used = generate_suggestion(profile, contact, purpose, channel, tone)
    return OutreachSuggestion(
        student_profile_id=student_profile_id,
        contact_id=contact_id,
        purpose=purpose,
        channel=channel,
        tone=tone,
        subject=subject,
        message=message,
        facts_used=facts_used,
        character_count=len(message),
        connection_note_limit=(300 if channel == "linkedin_connection_note" else None),
    )


@outreach_router.get("/{draft_id}", response_model=OutreachDraftResponse)
def get_outreach_draft(draft_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    return draft_or_404(db, draft_id, user.id)


@outreach_router.patch("/{draft_id}", response_model=OutreachDraftResponse)
def update_outreach_draft(
    draft_id: int, payload: OutreachDraftUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    draft = draft_or_404(db, draft_id, user.id)
    values = payload.model_dump(exclude_unset=True)
    effective_channel = values.get("channel", draft.channel)
    effective_message = values.get("message", draft.message)
    if (
        effective_channel == "linkedin_connection_note"
        and len(effective_message) > CONNECTION_NOTE_LIMIT
    ):
        raise HTTPException(
            status_code=422,
            detail="linkedin_connection_note messages must be 300 characters or fewer",
        )
    for field, value in values.items():
        setattr(draft, field, value)
    db.commit()
    db.refresh(draft)
    return draft


@outreach_router.delete("/{draft_id}", status_code=204)
def delete_outreach_draft(draft_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    draft = draft_or_404(db, draft_id, user.id)
    if draft.status != OutreachDraftStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="Only draft outreach messages can be deleted")
    db.delete(draft)
    db.commit()


def make_action(target: OutreachDraftStatus):
    def action(draft_id: int, user: CurrentUser, db: Session = Depends(get_db)):
        draft = draft_or_404(db, draft_id, user.id)
        transition(draft, target)
        db.commit()
        db.refresh(draft)
        return draft

    return action


for _action, _target in (
    ("approve", OutreachDraftStatus.APPROVED),
    ("copied", OutreachDraftStatus.COPIED),
    ("sent-manually", OutreachDraftStatus.SENT_MANUALLY),
    ("replied", OutreachDraftStatus.REPLIED),
    ("archive", OutreachDraftStatus.ARCHIVED),
):
    outreach_router.post(
        f"/{{draft_id}}/{_action}",
        response_model=OutreachDraftResponse,
        status_code=200,
    )(make_action(_target))
