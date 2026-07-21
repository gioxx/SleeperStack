import pytest
from fastapi.testclient import TestClient

import app.db as db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-value")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret-pass")

    db_path = str(tmp_path / "test.db")
    engine = db_module.make_engine(db_path=db_path)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", db_module.sessionmaker(bind=engine))

    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as test_client:
        test_client.post("/login", data={"username": "admin", "password": "s3cret-pass"})
        test_client.post(
            "/endpoints",
            data={
                "name": "lab",
                "portainer_url": "http://portainer.local:9000/api",
                "api_key": "my-secret-key",
                "endpoint_id": "2",
            },
        )
        yield test_client


def containers_url():
    return "http://portainer.local:9000/api/endpoints/2/docker/containers/json?all=true"


def test_dashboard_lists_only_labeled_containers(client, requests_mock):
    requests_mock.get(
        containers_url(),
        json=[
            {"Id": "abc", "Names": ["/night-app"], "State": "running", "Labels": {"autoshutdown": "night"}},
            {"Id": "def", "Names": ["/other-app"], "State": "running", "Labels": {}},
        ],
    )

    response = client.get("/dashboard")

    assert "night-app" in response.text
    assert "other-app" not in response.text


def test_dashboard_shows_connection_error(client, requests_mock):
    requests_mock.get(containers_url(), status_code=401, text="unauthorized")

    response = client.get("/dashboard")

    assert "Connection error" in response.text


def test_manual_stop_action_logs_run_history(client, requests_mock):
    requests_mock.post(
        "http://portainer.local:9000/api/endpoints/2/docker/containers/abc/stop", status_code=204
    )

    response = client.post("/dashboard/1/containers/abc/stop", follow_redirects=False)
    assert response.status_code == 303

    history_response = client.get("/history")
    assert "success" in history_response.text
