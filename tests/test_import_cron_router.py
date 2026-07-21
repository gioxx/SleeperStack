import pytest
from fastapi.testclient import TestClient

import app.db as db_module

SAMPLE_LINE = (
    "0 22 * * * docker run --rm -e PORTAINER_URL=http://portainer.local:9000/api "
    "-e PORTAINER_API_KEY=abc123 -e PORTAINER_ENDPOINT_ID=2 "
    "-e TARGET_LABEL=autoshutdown=night -e ACTION=stop gfsolone/sleeperstack"
)


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
        yield test_client


def test_preview_reports_missing_endpoint_when_none_configured(client):
    response = client.post("/rules/import/preview", data={"crontab_text": SAMPLE_LINE})

    assert "No configured endpoint matches" in response.text


def test_preview_matches_existing_endpoint_and_confirm_creates_rule(client):
    client.post(
        "/endpoints",
        data={
            "name": "lab",
            "portainer_url": "http://portainer.local:9000/api",
            "api_key": "my-secret-key",
            "endpoint_id": "2",
        },
    )

    preview_response = client.post("/rules/import/preview", data={"crontab_text": SAMPLE_LINE})
    assert "lab" in preview_response.text
    assert "Confirm import of 1 rule(s)" in preview_response.text

    confirm_response = client.post(
        "/rules/import/confirm",
        data={
            "cron_expression": ["0 22 * * *"],
            "action": ["stop"],
            "target_label": ["autoshutdown=night"],
            "endpoint_db_id": ["1"],
        },
        follow_redirects=False,
    )
    assert confirm_response.status_code == 303

    rules_response = client.get("/rules")
    assert "autoshutdown=night" in rules_response.text

    from app.main import app as fastapi_app

    assert fastapi_app.state.scheduler.scheduler.get_job("rule-1") is not None
