from datetime import datetime
from enum import StrEnum
from typing import Literal

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


SourceType = Literal["manual", "csv"]


class ContactBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    current_role: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    school: str | None = Field(default=None, max_length=160)
    skills_summary: str | None = Field(default=None, max_length=3000)
    profile_url: str | None = Field(default=None, max_length=500)
    source_type: SourceType
    source_name: str = Field(min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("full_name", "source_name")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("profile_url")
    @classmethod
    def reference_url_only(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("profile_url must be an http or https reference")
        return value


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    current_role: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    school: str | None = Field(default=None, max_length=160)
    skills_summary: str | None = Field(default=None, max_length=3000)
    profile_url: str | None = Field(default=None, max_length=500)
    source_name: str | None = Field(default=None, min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)


class ContactResponse(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ContactPage(BaseModel):
    items: list[ContactResponse]
    page: int
    page_size: int
    total: int


class CsvImportError(BaseModel):
    row: int
    message: str


class CsvImportSummary(BaseModel):
    created: int
    errors: list[CsvImportError]


class MatchBreakdown(BaseModel):
    role: float
    industry: float
    location: float
    school: float
    skills: float


class ContactMatch(BaseModel):
    contact: ContactResponse
    total_score: float
    breakdown: MatchBreakdown
    reasons: list[str]


class OutreachDraftStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    COPIED = "copied"
    SENT_MANUALLY = "sent_manually"
    REPLIED = "replied"
    ARCHIVED = "archived"


OutreachPurpose = Literal[
    "informational_interview",
    "career_advice",
    "project_collaboration",
    "internship_question",
    "general_networking",
]
OutreachChannel = Literal["linkedin_connection_note", "linkedin_message", "email", "other"]
OutreachTone = Literal["professional", "warm", "concise"]


class OutreachDraftCreate(BaseModel):
    student_profile_id: int = Field(gt=0)
    contact_id: int = Field(gt=0)
    purpose: OutreachPurpose
    channel: OutreachChannel
    tone: OutreachTone
    subject: str | None = Field(default=None, max_length=240)
    message: str = Field(min_length=1, max_length=10000)
    user_notes: str | None = Field(default=None, max_length=4000)

    @field_validator("subject", "user_notes")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None and value.strip() else None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class OutreachDraftUpdate(BaseModel):
    purpose: OutreachPurpose | None = None
    channel: OutreachChannel | None = None
    tone: OutreachTone | None = None
    subject: str | None = Field(default=None, max_length=240)
    message: str | None = Field(default=None, max_length=10000)
    user_notes: str | None = Field(default=None, max_length=4000)

    @field_validator("subject", "user_notes")
    @classmethod
    def trim_update_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None and value.strip() else None

    @field_validator("message")
    @classmethod
    def require_update_message(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class OutreachDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    contact_id: int
    purpose: OutreachPurpose
    channel: OutreachChannel
    tone: OutreachTone
    subject: str | None
    message: str
    status: OutreachDraftStatus
    user_notes: str | None
    created_at: datetime
    updated_at: datetime
    copied_at: datetime | None = None
    sent_manually_at: datetime | None = None
    replied_at: datetime | None = None


class OutreachDraftPage(BaseModel):
    items: list[OutreachDraftResponse]
    page: int
    page_size: int
    total: int


class OutreachSuggestion(BaseModel):
    student_profile_id: int
    contact_id: int
    purpose: OutreachPurpose
    channel: OutreachChannel
    tone: OutreachTone
    subject: str | None
    message: str
    facts_used: list[str]
    character_count: int
    connection_note_limit: int | None
    is_rule_based: bool = True


class OutreachActivitySummary(BaseModel):
    total: int
    by_status: dict[OutreachDraftStatus, int]
