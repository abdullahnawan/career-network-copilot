from datetime import date, datetime
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


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("display_name")
    @classmethod
    def display_name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("must be a valid email")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=128)


class PasswordConfirmation(BaseModel):
    password: str = Field(min_length=10, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    display_name: str
    created_at: datetime


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


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    ONLINE_ASSESSMENT = "online_assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


ApplicationSource = Literal["co_op_board", "company_site", "job_board", "referral", "other"]


def _clean_optional(value: str | None) -> str | None:
    return value.strip() if value is not None and value.strip() else None


def _posting_url(value: str | None) -> str | None:
    if value is not None and not value.startswith(("http://", "https://")):
        raise ValueError("posting_url must be an http or https link")
    return value


class JobApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=160)
    role_title: str = Field(min_length=1, max_length=160)
    posting_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=160)
    source: ApplicationSource = "company_site"
    resume_version: str | None = Field(default=None, max_length=60)
    referral_contact_id: int | None = Field(default=None, gt=0)
    deadline: date | None = None
    notes: str | None = Field(default=None, max_length=4000)
    status: Literal[ApplicationStatus.SAVED, ApplicationStatus.APPLIED] = ApplicationStatus.SAVED
    applied_at: datetime | None = None

    @field_validator("company", "role_title")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("posting_url", "location", "resume_version", "notes")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return _clean_optional(value)

    @field_validator("posting_url")
    @classmethod
    def link_only(cls, value: str | None) -> str | None:
        return _posting_url(value)

    @model_validator(mode="after")
    def applied_at_requires_applied(self) -> "JobApplicationCreate":
        if self.applied_at is not None and self.status != ApplicationStatus.APPLIED:
            raise ValueError("applied_at can only be set when status is applied")
        return self


class JobApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=160)
    role_title: str | None = Field(default=None, min_length=1, max_length=160)
    posting_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=160)
    source: ApplicationSource | None = None
    resume_version: str | None = Field(default=None, max_length=60)
    referral_contact_id: int | None = Field(default=None, gt=0)
    deadline: date | None = None
    notes: str | None = Field(default=None, max_length=4000)
    applied_at: datetime | None = None

    @field_validator("company", "role_title")
    @classmethod
    def required_update_text(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("posting_url", "location", "resume_version", "notes")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return _clean_optional(value)

    @field_validator("posting_url")
    @classmethod
    def link_only(cls, value: str | None) -> str | None:
        return _posting_url(value)


class JobApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role_title: str
    posting_url: str | None
    location: str | None
    source: ApplicationSource
    resume_version: str | None
    referral_contact_id: int | None
    deadline: date | None
    notes: str | None
    status: ApplicationStatus
    applied_at: datetime | None = None
    online_assessment_at: datetime | None = None
    interview_at: datetime | None = None
    offer_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class JobApplicationPage(BaseModel):
    items: list[JobApplicationResponse]
    page: int
    page_size: int
    total: int


class FunnelStats(BaseModel):
    applied: int
    online_assessment: int
    interview: int
    offer: int
    positive_response_rate: float


class ApplicationSummary(BaseModel):
    total: int
    by_status: dict[ApplicationStatus, int]
    funnel: FunnelStats
    by_resume_version: dict[str, FunnelStats]
    by_source: dict[str, FunnelStats]
    referral: FunnelStats
    cold: FunnelStats


FollowUpKind = Literal["application_no_response", "outreach_no_reply", "deadline_soon"]


class FollowUpItem(BaseModel):
    kind: FollowUpKind
    title: str
    detail: str
    application_id: int | None = None
    outreach_draft_id: int | None = None
    since: datetime | None = None
    due: date | None = None


class FollowUpList(BaseModel):
    items: list[FollowUpItem]
    application_days: int
    outreach_days: int
    deadline_days: int
