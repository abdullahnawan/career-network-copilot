from collections.abc import Generator
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import JobApplication, OutreachDraft

test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def database() -> Generator[None, None, None]:
    Base.metadata.create_all(test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


def contact_payload(name: str = "Fictional Engineer") -> dict:
    return {
        "full_name": name,
        "current_role": "Software Engineer",
        "company": "Example Bank",
        "source_type": "manual",
        "source_name": "Test notes",
    }


def application(client: TestClient, **overrides) -> dict:
    payload = {"company": "Example Bank", "role_title": "Software Developer Intern"}
    payload.update(overrides)
    response = client.post("/applications", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_defaults_to_saved_and_trims_text() -> None:
    client = TestClient(app)
    created = application(client, company="  Example Bank  ", notes="   ")
    assert created["status"] == "saved"
    assert created["company"] == "Example Bank"
    assert created["notes"] is None
    assert created["applied_at"] is None
    assert created["source"] == "company_site"


def test_create_as_applied_records_timestamp_and_backdating() -> None:
    client = TestClient(app)
    now_applied = application(client, status="applied")
    assert now_applied["applied_at"] is not None
    past = "2026-09-01T12:00:00Z"
    backdated = application(client, status="applied", applied_at=past)
    assert backdated["applied_at"].startswith("2026-09-01")


def test_validation_rejects_bad_input() -> None:
    client = TestClient(app)
    assert client.post("/applications", json={"company": " ", "role_title": "x"}).status_code == 422
    bad_link = {"company": "A", "role_title": "B", "posting_url": "javascript:alert(1)"}
    assert client.post("/applications", json=bad_link).status_code == 422
    early_date = {"company": "A", "role_title": "B", "applied_at": "2026-09-01T00:00:00Z"}
    assert client.post("/applications", json=early_date).status_code == 422
    assert client.post("/applications", json={**bad_link, "posting_url": None,
                                              "status": "offer"}).status_code == 422


def test_full_pipeline_with_guarded_transitions() -> None:
    client = TestClient(app)
    app_id = application(client)["id"]
    assert client.post(f"/applications/{app_id}/offer").status_code == 409
    applied = client.post(f"/applications/{app_id}/apply").json()
    assert applied["status"] == "applied" and applied["applied_at"]
    assessed = client.post(f"/applications/{app_id}/online-assessment").json()
    assert assessed["online_assessment_at"]
    interview = client.post(f"/applications/{app_id}/interview").json()
    assert interview["interview_at"]
    offer = client.post(f"/applications/{app_id}/offer").json()
    assert offer["status"] == "offer" and offer["offer_at"]
    withdrawn = client.post(f"/applications/{app_id}/withdraw").json()
    assert withdrawn["status"] == "withdrawn" and withdrawn["closed_at"]
    assert client.post(f"/applications/{app_id}/interview").status_code == 409


def test_update_rules() -> None:
    client = TestClient(app)
    saved = application(client)
    response = client.patch(
        f"/applications/{saved['id']}", json={"applied_at": "2026-09-01T00:00:00Z"}
    )
    assert response.status_code == 409
    updated = client.patch(
        f"/applications/{saved['id']}",
        json={
            "notes": "Ask about team placement",
            "resume_version": "SWE",
            "deadline": "2026-11-01",
        },
    ).json()
    assert updated["notes"] == "Ask about team placement"
    assert updated["deadline"] == "2026-11-01"
    assert client.patch(f"/applications/{saved['id']}", json={"company": ""}).status_code == 422


def test_referral_contact_must_be_owned_and_is_unlinked_on_delete() -> None:
    client = TestClient(app)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    linked = application(client, referral_contact_id=contact_id, source="referral")
    assert linked["referral_contact_id"] == contact_id
    assert client.post(
        "/applications", json={"company": "A", "role_title": "B", "referral_contact_id": 9999}
    ).status_code == 404

    other = TestClient(app)
    other_contact = other.post("/contacts", json=contact_payload("Someone Else")).json()["id"]
    assert client.patch(
        f"/applications/{linked['id']}", json={"referral_contact_id": other_contact}
    ).status_code == 404

    assert client.delete(f"/contacts/{contact_id}").status_code == 204
    assert client.get(f"/applications/{linked['id']}").json()["referral_contact_id"] is None


def test_applications_are_isolated_between_users() -> None:
    owner = TestClient(app)
    intruder = TestClient(app)
    app_id = application(owner)["id"]
    assert intruder.get(f"/applications/{app_id}").status_code == 404
    assert intruder.post(f"/applications/{app_id}/apply").status_code == 404
    assert intruder.delete(f"/applications/{app_id}").status_code == 404
    assert intruder.get("/applications").json()["total"] == 0


def test_list_filters_search_and_pagination() -> None:
    client = TestClient(app)
    application(client, company="Northwind", role_title="Data Engineer Intern",
                resume_version="Data", status="applied")
    application(client, company="Contoso", role_title="Backend Developer Co-op",
                resume_version="SWE")
    application(client, company="Fabrikam", role_title="Software Intern",
                resume_version="SWE", source="co_op_board")
    assert client.get("/applications", params={"status": "applied"}).json()["total"] == 1
    assert client.get("/applications", params={"resume_version": "SWE"}).json()["total"] == 2
    assert client.get("/applications", params={"source": "co_op_board"}).json()["total"] == 1
    assert client.get("/applications", params={"q": "data"}).json()["total"] == 1
    page = client.get("/applications", params={"page_size": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 2


def test_summary_funnel_by_version_and_referral() -> None:
    client = TestClient(app)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    a = application(client, resume_version="SWE", status="applied",
                    referral_contact_id=contact_id)["id"]
    b = application(client, resume_version="SWE", status="applied")["id"]
    application(client, resume_version="Data", status="applied")
    application(client, resume_version="Data")
    client.post(f"/applications/{a}/interview")
    client.post(f"/applications/{a}/offer")
    client.post(f"/applications/{b}/reject")

    summary = client.get("/applications/summary").json()
    assert summary["total"] == 4
    assert summary["by_status"]["saved"] == 1
    assert summary["by_status"]["offer"] == 1
    assert summary["funnel"]["applied"] == 3
    assert summary["funnel"]["interview"] == 1
    assert summary["funnel"]["offer"] == 1
    assert summary["funnel"]["positive_response_rate"] == pytest.approx(0.333)
    assert summary["by_resume_version"]["SWE"]["applied"] == 2
    assert summary["by_resume_version"]["SWE"]["positive_response_rate"] == 0.5
    assert summary["by_resume_version"]["Data"]["applied"] == 1
    assert summary["referral"]["applied"] == 1
    assert summary["referral"]["offer"] == 1
    assert summary["cold"]["applied"] == 2


def test_follow_ups_cover_stale_applications_outreach_and_deadlines() -> None:
    client = TestClient(app)
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    stale = application(client, company="Stale Corp", status="applied", applied_at=old)
    application(client, company="Fresh Corp", status="applied", applied_at=recent)
    soon = (date.today() + timedelta(days=2)).isoformat()
    later = (date.today() + timedelta(days=40)).isoformat()
    due = application(client, company="Deadline Inc", deadline=soon)
    application(client, company="Later Inc", deadline=later)

    profile_id = client.post(
        "/student-profiles",
        json={"full_name": "Fictional Student",
              "career_goals": [{"role": "Software Engineer", "goal_type": "internship"}]},
    ).json()["id"]
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    draft_id = client.post(
        "/outreach-drafts",
        json={"student_profile_id": profile_id, "contact_id": contact_id,
              "purpose": "internship_question", "channel": "linkedin_message",
              "tone": "warm", "message": "Hi there"},
    ).json()["id"]
    for step in ("approve", "copied", "sent-manually"):
        client.post(f"/outreach-drafts/{draft_id}/{step}")

    result = client.get("/follow-ups").json()
    kinds = {(item["kind"], item.get("application_id") or item.get("outreach_draft_id"))
             for item in result["items"]}
    assert ("application_no_response", stale["id"]) in kinds
    assert ("deadline_soon", due["id"]) in kinds
    assert all("Fresh Corp" not in item["title"] for item in result["items"])
    assert all("Later Inc" not in item["title"] for item in result["items"])
    assert result["items"][0]["kind"] == "deadline_soon"
    assert all(item["kind"] != "outreach_no_reply" for item in result["items"])
    assert client.get("/follow-ups", params={"outreach_days": 0}).status_code == 422

    with TestSession() as db:
        draft = db.get(OutreachDraft, draft_id)
        draft.sent_manually_at = datetime.now(timezone.utc) - timedelta(days=10)
        db.commit()
    nudges = [
        item for item in client.get("/follow-ups").json()["items"]
        if item["kind"] == "outreach_no_reply"
    ]
    assert nudges and nudges[0]["outreach_draft_id"] == draft_id
    assert "Fictional Engineer" in nudges[0]["title"]


def test_privacy_export_and_account_deletion_include_applications() -> None:
    client = TestClient(app)
    application(client, company="Exported Co")
    exported = client.get("/privacy/export").json()
    assert exported["applications"][0]["company"] == "Exported Co"
    deleted = client.request(
        "DELETE",
        "/account",
        json={"password": "correct horse battery"},
        headers={"origin": "http://localhost:3000"},
    )
    assert deleted.status_code == 204
    with TestSession() as db:
        assert db.scalar(select(func.count()).select_from(JobApplication)) == 0
