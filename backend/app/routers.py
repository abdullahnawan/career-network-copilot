from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import CareerGoal, Skill, StudentProfile, StudentSkill
from app.schemas import (
    CareerGoalCreate,
    CareerGoalResponse,
    CareerGoalUpdate,
    SkillInput,
    SkillListRequest,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/student-profiles", tags=["student profiles"])


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
