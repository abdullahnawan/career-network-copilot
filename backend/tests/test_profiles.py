from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def database() -> Generator[None, None, None]:
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_profile_lifecycle_with_goals_and_skills() -> None:
    client = TestClient(app)
    response = client.post(
        "/student-profiles",
        json={
            "full_name": "Demo Student",
            "school": "Fictional University",
            "graduation_year": 2027,
            "career_goals": [
                {"role": "Data Engineer", "goal_type": "internship", "industry": "Technology"}
            ],
            "skills": [{"name": "Python", "proficiency_level": "intermediate"}],
        },
    )
    assert response.status_code == 201
    profile = response.json()
    assert profile["career_goals"][0]["role"] == "Data Engineer"
    assert profile["skills"][0]["name"] == "Python"

    updated = client.patch(
        f"/student-profiles/{profile['id']}", json={"bio": "Interested in data systems."}
    )
    assert updated.status_code == 200
    assert updated.json()["bio"] == "Interested in data systems."

    replaced = client.put(
        f"/student-profiles/{profile['id']}/skills",
        json={"skills": [{"name": "SQL", "proficiency_level": "beginner"}]},
    )
    assert replaced.status_code == 200
    assert [skill["name"] for skill in replaced.json()["skills"]] == ["SQL"]


def test_profile_validation_and_not_found_responses() -> None:
    client = TestClient(app)
    invalid = client.post("/student-profiles", json={"full_name": "   "})
    assert invalid.status_code == 422

    missing = client.get("/student-profiles/999")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Student profile not found"}


def test_goal_management() -> None:
    client = TestClient(app)
    profile = client.post(
        "/student-profiles", json={"full_name": "Demo Student"}
    ).json()
    goal = client.post(
        f"/student-profiles/{profile['id']}/career-goals",
        json={"role": "Product Designer", "goal_type": "mentorship"},
    ).json()
    assert goal["role"] == "Product Designer"

    edited = client.patch(
        f"/student-profiles/{profile['id']}/career-goals/{goal['id']}",
        json={"notes": "Learn about the field"},
    )
    assert edited.status_code == 200
    assert edited.json()["notes"] == "Learn about the field"

    deleted = client.delete(f"/student-profiles/{profile['id']}/career-goals/{goal['id']}")
    assert deleted.status_code == 204
