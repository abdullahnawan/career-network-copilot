import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.matching import calculate_match
from app.models import CareerGoal, Contact, Skill, StudentProfile, StudentSkill
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
    SkillInput,
    SkillListRequest,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/student-profiles", tags=["student profiles"])
contacts_router = APIRouter(prefix="/contacts", tags=["contacts"])

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 500
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


def profile_query(profile_id: int):
    return (
        select(StudentProfile)
        .where(StudentProfile.id == profile_id)
        .options(
            selectinload(StudentProfile.career_goals),
            selectinload(StudentProfile.skills).selectinload(StudentSkill.skill),
        )
    )


def get_profile_or_404(db: Session, profile_id: int) -> StudentProfile:
    profile = db.scalar(profile_query(profile_id))
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
def create_profile(payload: StudentProfileCreate, db: Session = Depends(get_db)):
    profile = StudentProfile(**payload.model_dump(exclude={"career_goals", "skills"}))
    profile.career_goals = [CareerGoal(**goal.model_dump()) for goal in payload.career_goals]
    db.add(profile)
    db.flush()
    add_skills(db, profile, payload.skills)
    db.commit()
    return get_profile_or_404(db, profile.id)


@router.get("/{profile_id}", response_model=StudentProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    return get_profile_or_404(db, profile_id)


@router.patch("/{profile_id}", response_model=StudentProfileResponse)
def update_profile(profile_id: int, payload: StudentProfileUpdate, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, profile_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    return get_profile_or_404(db, profile_id)


@router.post("/{profile_id}/career-goals", response_model=CareerGoalResponse, status_code=201)
def create_goal(profile_id: int, payload: CareerGoalCreate, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, profile_id)
    goal = CareerGoal(student_profile_id=profile.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{profile_id}/career-goals/{goal_id}", response_model=CareerGoalResponse)
def update_goal(
    profile_id: int, goal_id: int, payload: CareerGoalUpdate, db: Session = Depends(get_db)
):
    get_profile_or_404(db, profile_id)
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
def delete_goal(profile_id: int, goal_id: int, db: Session = Depends(get_db)):
    get_profile_or_404(db, profile_id)
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
    profile_id: int, payload: SkillListRequest, db: Session = Depends(get_db)
):
    profile = get_profile_or_404(db, profile_id)
    profile.skills.clear()
    db.flush()
    add_skills(db, profile, payload.skills)
    db.commit()
    return get_profile_or_404(db, profile_id)


@router.get("/{profile_id}/matches", response_model=list[ContactMatch])
def get_matches(profile_id: int, db: Session = Depends(get_db)):
    profile = get_profile_or_404(db, profile_id)
    contacts = db.scalars(select(Contact).order_by(Contact.created_at.desc())).all()
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


def contact_or_404(db: Session, contact_id: int) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@contacts_router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@contacts_router.get("", response_model=ContactPage)
def list_contacts(
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
    query = select(Contact).where(*filters).order_by(Contact.created_at.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    contacts = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return ContactPage(items=contacts, page=page, page_size=page_size, total=total)


@contacts_router.post("/import-csv", response_model=CsvImportSummary)
async def import_contacts_csv(
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
        db.add(Contact(**contact.model_dump()))
        created += 1
    db.commit()
    return CsvImportSummary(created=created, errors=errors)


@contacts_router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    return contact_or_404(db, contact_id)


@contacts_router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, payload: ContactUpdate, db: Session = Depends(get_db)):
    contact = contact_or_404(db, contact_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@contacts_router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = contact_or_404(db, contact_id)
    db.delete(contact)
    db.commit()
