from collections.abc import Generator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
            "career_goals": [
                {
                    "role": "Data Engineer",
                    "industry": "Technology",
                    "location": "Toronto",
                    "goal_type": "internship",
                }
            ],
            "skills": [{"name": "Python", "proficiency_level": "intermediate"}],
        },
    ).json()["id"]


def contact_payload(name: str = "Fictional Professional") -> dict:
    return {
        "full_name": name,
        "current_role": "Data Engineer",
        "company": "Example Labs",
        "industry": "Technology",
        "location": "Toronto",
        "school": "Example University",
        "skills_summary": "Python, SQL",
        "profile_url": "https://example.test/profile",
        "source_type": "manual",
        "source_name": "User-provided notes",
        "notes": "Fictional test record",
    }


def test_contact_crud_and_filters() -> None:
    client = TestClient(app)
    created = client.post("/contacts", json=contact_payload()).json()
    assert created["full_name"] == "Fictional Professional"
    listed = client.get("/contacts", params={"company": "Example", "page_size": 1})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]

    edited = client.patch(f"/contacts/{created['id']}", json={"notes": "Updated"})
    assert edited.status_code == 200
    assert edited.json()["notes"] == "Updated"
    assert client.get(f"/contacts/{created['id']}").status_code == 200
    assert client.delete(f"/contacts/{created['id']}").status_code == 204
    assert client.get(f"/contacts/{created['id']}").status_code == 404


def test_pagination_and_csv_validation() -> None:
    client = TestClient(app)
    client.post("/contacts", json=contact_payload("First Fictional Person"))
    client.post("/contacts", json=contact_payload("Second Fictional Person"))
    page = client.get("/contacts", params={"page": 2, "page_size": 1}).json()
    assert page["total"] == 2
    assert len(page["items"]) == 1

    csv_content = (
        "full_name,source_name,current_role,source_type\n"
        "CSV Fictional Person,Example spreadsheet,Designer,csv\n"
        "Bad Formula,Example spreadsheet,=HYPERLINK(\"x\"),csv\n"
        "Unsupported Source,Example spreadsheet,Designer,manual\n"
    ).encode()
    result = client.post(
        "/contacts/import-csv",
        files={"file": ("contacts.csv", BytesIO(csv_content), "text/csv")},
    )
    assert result.status_code == 200
    assert result.json()["created"] == 1
    assert len(result.json()["errors"]) == 2

    missing_headers = client.post(
        "/contacts/import-csv",
        files={"file": ("contacts.csv", BytesIO(b"company\nExample Labs\n"), "text/csv")},
    )
    assert missing_headers.status_code == 400


def test_matching_score_reasons_and_missing_profile() -> None:
    client = TestClient(app)
    profile_id = create_profile(client)
    client.post("/contacts", json=contact_payload())
    client.post(
        "/contacts",
        json={
            **contact_payload("Unrelated Fictional Person"),
            "current_role": "Writer",
            "industry": "Arts",
            "location": "Halifax",
            "school": "Other College",
            "skills_summary": "Illustration",
        },
    )
    matches = client.get(f"/student-profiles/{profile_id}/matches")
    assert matches.status_code == 200
    assert matches.json()[0]["total_score"] == 100
    assert "Matches your target role." in matches.json()[0]["reasons"]
    assert matches.json()[1]["total_score"] == 0
    assert client.get("/student-profiles/999/matches").status_code == 404
