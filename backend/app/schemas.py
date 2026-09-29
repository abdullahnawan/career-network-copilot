from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CareerGoalBase(BaseModel):
    role: str = Field(min_length=1, max_length=160)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    goal_type: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class CareerGoalCreate(CareerGoalBase):
    pass


class CareerGoalUpdate(BaseModel):
    role: str | None = Field(default=None, min_length=1, max_length=160)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    goal_type: str | None = Field(default=None, min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class CareerGoalResponse(CareerGoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    created_at: datetime


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    proficiency_level: str = Field(min_length=1, max_length=40)

    @field_validator("name", "proficiency_level")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class SkillListMixin(BaseModel):
    skills: list[SkillInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_skills(self):
        names = [skill.name.casefold() for skill in self.skills]
        if len(names) != len(set(names)):
            raise ValueError("skills must not contain duplicate names")
        return self


class SkillResponse(SkillInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class StudentSkillResponse(SkillResponse):
    pass


class StudentProfileBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    school: str | None = Field(default=None, max_length=160)
    program: str | None = Field(default=None, max_length=160)
    graduation_year: int | None = Field(default=None, ge=1900, le=2200)
    location: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=5000)

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("full_name must not be blank")
        return value


class StudentProfileCreate(StudentProfileBase, SkillListMixin):
    career_goals: list[CareerGoalCreate] = Field(default_factory=list)


class SkillListRequest(SkillListMixin):
    pass


class StudentProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    school: str | None = Field(default=None, max_length=160)
    program: str | None = Field(default=None, max_length=160)
    graduation_year: int | None = Field(default=None, ge=1900, le=2200)
    location: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=5000)


class StudentProfileResponse(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    career_goals: list[CareerGoalResponse] = Field(default_factory=list)
    skills: list[StudentSkillResponse] = Field(default_factory=list)
