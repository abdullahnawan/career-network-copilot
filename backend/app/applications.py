"""Job application pipeline and follow-up reminders.

Applications are entered and advanced by the user. Nothing here submits
applications or contacts employers; it only records what the user did.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.db import get_db
from app.models import (
    ApplicationStatus,
    Contact,
    JobApplication,
    OutreachDraft,
    OutreachDraftStatus,
)
from app.schemas import (
    ApplicationSource,
    ApplicationSummary,
    FollowUpItem,
    FollowUpList,
    FunnelStats,
    JobApplicationCreate,
    JobApplicationPage,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from app.schemas import ApplicationStatus as ApplicationStatusSchema

applications_router = APIRouter(prefix="/applications", tags=["applications"])
follow_ups_router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])

TERMINAL = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.SAVED: {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.APPLIED: {
        ApplicationStatus.ONLINE_ASSESSMENT,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.ONLINE_ASSESSMENT: {
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.INTERVIEW: {
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.OFFER: {ApplicationStatus.WITHDRAWN},
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.WITHDRAWN: set(),
}
TIMESTAMP_FIELDS = {
    ApplicationStatus.APPLIED: "applied_at",
    ApplicationStatus.ONLINE_ASSESSMENT: "online_assessment_at",
    ApplicationStatus.INTERVIEW: "interview_at",
    ApplicationStatus.OFFER: "offer_at",
    ApplicationStatus.REJECTED: "closed_at",
    ApplicationStatus.WITHDRAWN: "closed_at",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; treat them as UTC."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def application_or_404(db: Session, application_id: int, owner_id: int) -> JobApplication:
    application = db.scalar(
        select(JobApplication).where(
            JobApplication.id == application_id, JobApplication.owner_id == owner_id
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def ensure_contact_owned(db: Session, contact_id: int | None, owner_id: int) -> None:
    if contact_id is None:
        return
    found = db.scalar(
        select(Contact.id).where(Contact.id == contact_id, Contact.owner_id == owner_id)
    )
    if found is None:
        raise HTTPException(status_code=404, detail="Referral contact not found")


def transition(application: JobApplication, target: ApplicationStatus) -> None:
    current = ApplicationStatus(application.status)
    if target not in ALLOWED_TRANSITIONS[current]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move application from {current.value} to {target.value}",
        )
    application.status = target.value
    field = TIMESTAMP_FIELDS[target]
    if getattr(application, field) is None:
        setattr(application, field, _now())


@applications_router.post("", response_model=JobApplicationResponse, status_code=201)
def create_application(
    payload: JobApplicationCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_contact_owned(db, payload.referral_contact_id, user.id)
    values = payload.model_dump()
    if values["status"] == ApplicationStatus.APPLIED and values["applied_at"] is None:
        values["applied_at"] = _now()
    values["status"] = ApplicationStatus(values["status"]).value
    application = JobApplication(owner_id=user.id, **values)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@applications_router.get("", response_model=JobApplicationPage)
def list_applications(
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: ApplicationStatusSchema | None = Query(default=None, alias="status"),
    source: ApplicationSource | None = None,
    resume_version: str | None = Query(default=None, max_length=60),
    q: str | None = Query(default=None, max_length=160),
    db: Session = Depends(get_db),
):
    query = select(JobApplication).where(JobApplication.owner_id == user.id)
    if status_filter:
        query = query.where(JobApplication.status == status_filter.value)
    if source:
        query = query.where(JobApplication.source == source)
    if resume_version:
        query = query.where(JobApplication.resume_version == resume_version)
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(JobApplication.company).like(term),
                func.lower(JobApplication.role_title).like(term),
            )
        )
    query = query.order_by(JobApplication.updated_at.desc(), JobApplication.id.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return JobApplicationPage(items=items, page=page, page_size=page_size, total=total)


def _funnel(applications: list[JobApplication]) -> FunnelStats:
    applied = [a for a in applications if a.applied_at is not None]
    assessed = sum(1 for a in applied if a.online_assessment_at is not None)
    interviewed = sum(1 for a in applied if a.interview_at is not None)
    offers = sum(1 for a in applied if a.offer_at is not None)
    positive = sum(
        1
        for a in applied
        if a.online_assessment_at or a.interview_at or a.offer_at
    )
    rate = round(positive / len(applied), 3) if applied else 0.0
    return FunnelStats(
        applied=len(applied),
        online_assessment=assessed,
        interview=interviewed,
        offer=offers,
        positive_response_rate=rate,
    )


@applications_router.get("/summary", response_model=ApplicationSummary)
def application_summary(user: CurrentUser, db: Session = Depends(get_db)):
    applications = list(
        db.scalars(select(JobApplication).where(JobApplication.owner_id == user.id))
    )
    by_status = {item.value: 0 for item in ApplicationStatus}
    by_version: dict[str, list[JobApplication]] = defaultdict(list)
    by_source: dict[str, list[JobApplication]] = defaultdict(list)
    referral: list[JobApplication] = []
    cold: list[JobApplication] = []
    for application in applications:
        by_status[application.status] += 1
        by_version[application.resume_version or "unspecified"].append(application)
        by_source[application.source].append(application)
        if application.referral_contact_id is not None or application.source == "referral":
            referral.append(application)
        else:
            cold.append(application)
    return ApplicationSummary(
        total=len(applications),
        by_status=by_status,
        funnel=_funnel(applications),
        by_resume_version={key: _funnel(value) for key, value in sorted(by_version.items())},
        by_source={key: _funnel(value) for key, value in sorted(by_source.items())},
        referral=_funnel(referral),
        cold=_funnel(cold),
    )


@applications_router.get("/{application_id}", response_model=JobApplicationResponse)
def get_application(application_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    return application_or_404(db, application_id, user.id)


@applications_router.patch("/{application_id}", response_model=JobApplicationResponse)
def update_application(
    application_id: int,
    payload: JobApplicationUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    application = application_or_404(db, application_id, user.id)
    values = payload.model_dump(exclude_unset=True)
    if "referral_contact_id" in values:
        ensure_contact_owned(db, values["referral_contact_id"], user.id)
    if "applied_at" in values and application.status == ApplicationStatus.SAVED.value:
        raise HTTPException(
            status_code=409, detail="Mark the application as applied before setting applied_at"
        )
    if "applied_at" in values and values["applied_at"] is None:
        raise HTTPException(status_code=422, detail="applied_at cannot be cleared")
    for field, value in values.items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


@applications_router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    application = application_or_404(db, application_id, user.id)
    db.delete(application)
    db.commit()


def make_action(target: ApplicationStatus):
    def action(application_id: int, user: CurrentUser, db: Session = Depends(get_db)):
        application = application_or_404(db, application_id, user.id)
        transition(application, target)
        db.commit()
        db.refresh(application)
        return application

    return action


for _action, _target in (
    ("apply", ApplicationStatus.APPLIED),
    ("online-assessment", ApplicationStatus.ONLINE_ASSESSMENT),
    ("interview", ApplicationStatus.INTERVIEW),
    ("offer", ApplicationStatus.OFFER),
    ("reject", ApplicationStatus.REJECTED),
    ("withdraw", ApplicationStatus.WITHDRAWN),
):
    applications_router.post(
        f"/{{application_id}}/{_action}",
        response_model=JobApplicationResponse,
        status_code=200,
    )(make_action(_target))


@follow_ups_router.get("", response_model=FollowUpList)
def list_follow_ups(
    user: CurrentUser,
    application_days: int = Query(default=21, ge=1, le=365),
    outreach_days: int = Query(default=7, ge=1, le=365),
    deadline_days: int = Query(default=7, ge=0, le=365),
    db: Session = Depends(get_db),
):
    now = _now()
    today = now.date()
    items: list[FollowUpItem] = []

    waiting = db.scalars(
        select(JobApplication).where(
            JobApplication.owner_id == user.id,
            JobApplication.status == ApplicationStatus.APPLIED.value,
        )
    )
    for application in waiting:
        applied_at = _aware(application.applied_at)
        if applied_at is not None and applied_at <= now - timedelta(days=application_days):
            days = (now - applied_at).days
            items.append(
                FollowUpItem(
                    kind="application_no_response",
                    title=f"{application.company}: {application.role_title}",
                    detail=f"No response {days} days after applying. Consider a follow-up "
                    "or a referral.",
                    application_id=application.id,
                    since=applied_at,
                )
            )

    sent = db.scalars(
        select(OutreachDraft).where(
            OutreachDraft.owner_id == user.id,
            OutreachDraft.status == OutreachDraftStatus.SENT_MANUALLY.value,
        )
    )
    for draft in sent:
        sent_at = _aware(draft.sent_manually_at)
        if sent_at is not None and sent_at <= now - timedelta(days=outreach_days):
            days = (now - sent_at).days
            contact = draft.contact.full_name if draft.contact else "contact"
            items.append(
                FollowUpItem(
                    kind="outreach_no_reply",
                    title=f"Outreach to {contact}",
                    detail=f"No reply recorded {days} days after you sent it. A short, "
                    "polite nudge is reasonable.",
                    outreach_draft_id=draft.id,
                    since=sent_at,
                )
            )

    upcoming = db.scalars(
        select(JobApplication).where(
            JobApplication.owner_id == user.id,
            JobApplication.status == ApplicationStatus.SAVED.value,
            JobApplication.deadline.is_not(None),
        )
    )
    for application in upcoming:
        deadline: date = application.deadline
        if today <= deadline <= today + timedelta(days=deadline_days):
            remaining = (deadline - today).days
            when = "today" if remaining == 0 else f"in {remaining} day(s)"
            items.append(
                FollowUpItem(
                    kind="deadline_soon",
                    title=f"{application.company}: {application.role_title}",
                    detail=f"Saved but not applied. Deadline is {when}.",
                    application_id=application.id,
                    due=deadline,
                )
            )

    def sort_key(item: FollowUpItem) -> tuple[int, float]:
        if item.kind == "deadline_soon" and item.due is not None:
            return (0, float(item.due.toordinal()))
        return (1, item.since.timestamp() if item.since else 0.0)

    items.sort(key=sort_key)
    return FollowUpList(
        items=items,
        application_days=application_days,
        outreach_days=outreach_days,
        deadline_days=deadline_days,
    )
