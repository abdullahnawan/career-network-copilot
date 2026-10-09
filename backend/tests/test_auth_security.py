from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def register(client: TestClient, email: str) -> None:
    response = client.post(
        "/auth/register",
        headers={"origin": "http://localhost:3000"},
        json={"email": email, "display_name": "Test user", "password": "correct horse battery"},
    )
    assert response.status_code == 201


def test_auth_cookie_and_origin_validation(client: TestClient) -> None:
    blocked = client.post(
        "/auth/register",
        json={
            "email": "blocked@example.test",
            "display_name": "Blocked",
            "password": "correct horse battery",
        },
    )
    assert blocked.status_code == 403
    register(client, "one@example.test")
    assert client.get("/auth/me").status_code == 200
    logout = client.post("/auth/logout", headers={"origin": "http://localhost:3000"})
    assert logout.status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_ownership_isolation(client: TestClient) -> None:
    register(client, "owner@example.test")
    profile_response = client.post(
        "/student-profiles",
        headers={"origin": "http://localhost:3000"},
        json={"full_name": "Owned"},
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()
    client.post("/auth/logout", headers={"origin": "http://localhost:3000"})
    register(client, "other@example.test")
    assert client.get(f"/student-profiles/{profile['id']}").status_code == 404


def test_account_export_contains_owned_data(client: TestClient) -> None:
    register(client, "export@example.test")
    profile = client.post(
        "/student-profiles",
        headers={"origin": "http://localhost:3000"},
        json={
            "full_name": "Exported",
            "career_goals": [{"role": "Engineer", "goal_type": "job"}],
            "skills": [{"name": "Python", "proficiency_level": "advanced"}],
        },
    )
    assert profile.status_code == 201
    exported = client.get("/account/export")
    assert exported.status_code == 200
    record = exported.json()["student_profiles"][0]
    assert record["career_goals"][0]["role"] == "Engineer"
    assert record["skills"][0]["name"] == "Python"


def test_password_confirmation_required_for_account_deletion(client: TestClient) -> None:
    register(client, "delete@example.test")
    denied = client.request(
        "DELETE",
        "/account",
        headers={"origin": "http://localhost:3000"},
        json={"password": "wrong password"},
    )
    assert denied.status_code == 400
    allowed = client.request(
        "DELETE", "/account", headers={"origin": "http://localhost:3000"},
        json={"password": "correct horse battery"},
    )
    assert allowed.status_code == 204
    assert client.get("/auth/me").status_code == 401
