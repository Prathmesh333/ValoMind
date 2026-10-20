from fastapi.testclient import TestClient
from valomind.config import Settings
from valomind.main import create_app


def client(**kwargs):
    return TestClient(create_app(Settings(_env_file=None, **kwargs)))


def test_liveness():
    response = client().get("/api/v1/health/live")
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_demo_disabled_without_token():
    assert client().get("/api/v1/demo/match").status_code == 404


def test_demo_requires_bearer():
    response = client(demo_access_token="test-only").get("/api/v1/demo/match")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "UNAUTHORIZED"


def test_synthetic_fixture_and_rounds():
    response = client(demo_access_token="test-only").get(
        "/api/v1/demo/match", headers={"Authorization": "Bearer test-only"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["is_synthetic"] is True
    assert payload["data"]["is_synthetic"] is True
    assert len(payload["data"]["rounds"]) == 5
    assert all(p["is_synthetic"] for p in payload["data"]["players"])


def test_feature_flag_blocks_demo():
    response = client(demo_synthetic=False, demo_access_token="test-only").get(
        "/api/v1/demo/match", headers={"Authorization": "Bearer test-only"}
    )
    assert response.status_code == 404


def test_unknown_path_is_problem():
    response = client().get("/api/v1/players")
    assert response.status_code == 404
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_invalid_bearer_is_rejected():
    response = client(demo_access_token="test-only").get(
        "/api/v1/demo/match", headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401


def test_readiness_does_not_claim_success_without_database(monkeypatch):
    from sqlalchemy.exc import OperationalError

    class UnavailableEngine:
        disposed = False

        def connect(self):
            raise OperationalError("connect", {}, Exception("private connection detail"))

        def dispose(self):
            self.disposed = True

    engine = UnavailableEngine()
    monkeypatch.setattr("valomind.main.create_engine", lambda *args, **kwargs: engine)
    response = client().get("/api/v1/health/ready")
    assert response.status_code == 503
    assert "private connection detail" not in response.text
    assert engine.disposed
