from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

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

def create_profile(client: TestClient) -> int:
    return client.post(
        "/student-profiles",
        json={
            "full_name": "Fictional Student",
            "school": "Example University",
            "career_goals": [{"role": "Data Engineer", "goal_type": "internship"}],
        },
    ).json()["id"]


def contact_payload() -> dict:
    return {
        "full_name": "Fictional Professional",
        "current_role": "Data Engineer",
        "company": "Example Labs",
        "industry": "Technology",
        "source_type": "manual",
        "source_name": "Test notes",
    }


def test_suggestion_is_deterministic_and_not_saved() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    first = client.post(
        "/outreach-drafts/suggest",
        params={
            "student_profile_id": profile_id,
            "contact_id": contact_id,
            "purpose": "career_advice",
            "channel": "email",
            "tone": "warm",
        },
    )
    second = client.post(
        "/outreach-drafts/suggest",
        params={
            "student_profile_id": profile_id,
            "contact_id": contact_id,
            "purpose": "career_advice",
            "channel": "email",
            "tone": "warm",
        },
    )
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["facts_used"]
    assert "referral" not in first.json()["message"].lower()
    assert client.get("/outreach-drafts").json()["total"] == 0


def test_draft_lifecycle_and_draft_only_deletion() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    payload = {
        "student_profile_id": profile_id,
        "contact_id": contact_id,
        "purpose": "career_advice",
        "channel": "linkedin_message",
        "tone": "professional",
        "message": "A thoughtful note",
    }
    draft = client.post("/outreach-drafts", json=payload).json()
    draft_id = draft["id"]
    approved = client.post(f"/outreach-drafts/{draft_id}/approve")
    assert approved.json()["status"] == "approved"
    assert approved.json()["copied_at"] is None
    copied = client.post(f"/outreach-drafts/{draft_id}/copied")
    assert copied.json()["status"] == "copied"
    assert copied.json()["copied_at"] is not None
    sent = client.post(f"/outreach-drafts/{draft_id}/sent-manually")
    assert sent.json()["status"] == "sent_manually"
    assert sent.json()["sent_manually_at"] is not None
    replied = client.post(f"/outreach-drafts/{draft_id}/replied")
    assert replied.json()["status"] == "replied"
    assert replied.json()["replied_at"] is not None
    assert client.delete(f"/outreach-drafts/{draft_id}").status_code == 409
    archived = client.post(f"/outreach-drafts/{draft_id}/archive")
    assert archived.json()["status"] == "archived"
    summary = client.get("/outreach-drafts/activity-summary").json()
    assert summary["total"] == 1
    assert summary["by_status"]["archived"] == 1


def test_invalid_transition_and_pagination_filter() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    payload = {
        "student_profile_id": profile_id,
        "contact_id": contact_id,
        "purpose": "career_advice",
        "channel": "linkedin_message",
        "tone": "professional",
        "message": "A note",
    }
    draft = client.post("/outreach-drafts", json=payload).json()
    assert client.post(f"/outreach-drafts/{draft['id']}/replied").status_code == 409
    listed = client.get("/outreach-drafts", params={"status": "draft", "page_size": 1})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert client.delete(f"/outreach-drafts/{draft['id']}").status_code == 204


def test_invalid_transition_returns_conflict() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    draft = client.post(
        "/outreach-drafts",
        json={
            "student_profile_id": profile_id,
            "contact_id": contact_id,
            "purpose": "career_advice",
            "channel": "linkedin_message",
            "tone": "professional",
            "message": "A note",
        },
    ).json()

    response = client.post(f"/outreach-drafts/{draft['id']}/replied")

    assert response.status_code == 409
    assert "Cannot transition" in response.json()["detail"]


def test_connection_note_limits_and_blank_update_validation() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    contact_id = client.post("/contacts", json=contact_payload()).json()["id"]
    base = {
        "student_profile_id": profile_id,
        "contact_id": contact_id,
        "purpose": "career_advice",
        "channel": "linkedin_connection_note",
        "tone": "professional",
    }
    oversized = client.post("/outreach-drafts", json={**base, "message": "x" * 301})
    assert oversized.status_code == 422
    assert "300 characters" in oversized.json()["detail"]

    draft = client.post("/outreach-drafts", json={**base, "message": "A valid note"}).json()
    too_long = client.patch(
        f"/outreach-drafts/{draft['id']}", json={"message": "x" * 301}
    )
    assert too_long.status_code == 422
    blank_update = client.patch(
        f"/outreach-drafts/{draft['id']}", json={"message": "  "}
    )
    assert blank_update.status_code == 422
    assert client.patch(
        f"/outreach-drafts/{draft['id']}", json={"tone": "warm"}
    ).status_code == 200
