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


def test_create_rule_registers_scheduler_job(client):
    from app.main import app as fastapi_app

    response = client.post(
        "/rules",
        data={
            "endpoint_id": 1,
            "target_label": "autoshutdown=night",
            "action": "stop",
            "cron_expression": "0 22 * * *",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    scheduler = fastapi_app.state.scheduler
    assert scheduler.scheduler.get_job("rule-1") is not None

    list_response = client.get("/rules")
    assert "autoshutdown=night" in list_response.text


def test_create_rule_rejects_invalid_cron(client):
    response = client.post(
        "/rules",
        data={
            "endpoint_id": 1,
            "target_label": "autoshutdown=night",
            "action": "stop",
            "cron_expression": "not-a-cron",
        },
    )
    assert response.status_code == 400
    assert "Invalid cron expression" in response.text


def test_toggle_rule_disables_and_removes_job(client):
    from app.main import app as fastapi_app

    client.post(
        "/rules",
        data={
            "endpoint_id": 1,
            "target_label": "autoshutdown=night",
            "action": "stop",
            "cron_expression": "0 22 * * *",
        },
    )
    scheduler = fastapi_app.state.scheduler
    assert scheduler.scheduler.get_job("rule-1") is not None

    client.post("/rules/1/toggle")
    assert scheduler.scheduler.get_job("rule-1") is None

    client.post("/rules/1/toggle")
    assert scheduler.scheduler.get_job("rule-1") is not None


def test_delete_rule_removes_job_and_row(client):
    from app.main import app as fastapi_app

    client.post(
        "/rules",
        data={
            "endpoint_id": 1,
            "target_label": "autoshutdown=night",
            "action": "stop",
            "cron_expression": "0 22 * * *",
        },
    )
    scheduler = fastapi_app.state.scheduler

    client.post("/rules/1/delete")

    assert scheduler.scheduler.get_job("rule-1") is None
    list_response = client.get("/rules")
    assert "<td>autoshutdown=night</td>" not in list_response.text
