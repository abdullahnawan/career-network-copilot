from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import CurrentUser, validate_origin
from app.config import get_settings
from app.db import get_db
from app.models import Contact, OutreachDraft, StudentProfile, UserSession
from app.schemas import PasswordConfirmation

router = APIRouter(prefix="/privacy", tags=["privacy"])
account_router = APIRouter(tags=["privacy"])


@router.get("/export")
@router.get("/account/export", include_in_schema=False)
@account_router.get("/account/export", include_in_schema=False)
def export_data(user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    contacts = db.scalars(select(Contact).where(Contact.owner_id == user.id)).all()
    profiles = db.scalars(select(StudentProfile).where(StudentProfile.owner_id == user.id)).all()
    drafts = db.scalars(select(OutreachDraft).where(OutreachDraft.owner_id == user.id)).all()
    return {
        "user": {"id": user.id, "email": user.email},
        "student_profiles": [
            {
                "id": p.id,
                "full_name": p.full_name,
                "school": p.school,
                "program": p.program,
                "career_goals": [
                    {
                        "role": g.role,
                        "industry": g.industry,
                        "location": g.location,
                        "goal_type": g.goal_type,
                        "notes": g.notes,
                    }
                    for g in p.career_goals
                ],
                "skills": [
                    {"name": s.skill.name, "proficiency_level": s.proficiency_level}
                    for s in p.skills
                ],
            }
            for p in profiles
        ],
        "contacts": [
            {"id": c.id, "full_name": c.full_name, "company": c.company} for c in contacts
        ],
        "outreach_drafts": [{"id": d.id, "message": d.message, "status": d.status} for d in drafts],
    }


@router.delete("/account", status_code=204, dependencies=[Depends(validate_origin)])
@account_router.delete("/account", status_code=204, dependencies=[Depends(validate_origin)])
def delete_account(
    response: Response,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    payload: PasswordConfirmation,
):
    from app.auth import verify_password

    if not verify_password(payload.password, user.password_hash):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Password confirmation failed")
    db.execute(delete(OutreachDraft).where(OutreachDraft.owner_id == user.id))
    db.execute(delete(Contact).where(Contact.owner_id == user.id))
    db.execute(delete(StudentProfile).where(StudentProfile.owner_id == user.id))
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.delete(user)
    db.commit()
    response.delete_cookie(get_settings().session_cookie_name)
