from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def authenticate_legacy_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    original_request = TestClient.request

    def request_with_test_user(self, method, url, **kwargs):
        if (
            url not in {"/health"}
            and not url.startswith("/auth/")
            and not getattr(self, "_phase7_authenticated", False)
        ):
            original_request(
                self,
                "POST",
                "/auth/register",
                headers={"origin": "http://localhost:3000"},
                json={
                    "email": f"{uuid4().hex}@example.test",
                    "display_name": "Legacy test user",
                    "password": "correct horse battery",
                },
            )
            self._phase7_authenticated = True
        if (
            url not in {"/health"}
            and not url.startswith("/auth/")
            and method.upper() not in {"GET", "HEAD", "OPTIONS"}
        ):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("origin", "http://localhost:3000")
            kwargs["headers"] = headers
        return original_request(self, method, url, **kwargs)

    monkeypatch.setattr(TestClient, "request", request_with_test_user)
