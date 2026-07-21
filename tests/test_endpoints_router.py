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
        yield test_client


def test_create_and_list_endpoint(client):
    response = client.post(
        "/endpoints",
        data={
            "name": "lab",
            "portainer_url": "http://portainer.local:9000/api/",
            "api_key": "my-secret-key",
            "endpoint_id": "2",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    list_response = client.get("/endpoints")
    assert "lab" in list_response.text
    assert "http://portainer.local:9000/api" in list_response.text
    assert "my-secret-key" not in list_response.text


def test_test_endpoint_reports_connection_result(client, requests_mock):
    client.post(
        "/endpoints",
        data={
            "name": "lab",
            "portainer_url": "http://portainer.local:9000/api",
            "api_key": "my-secret-key",
            "endpoint_id": "2",
        },
    )
    endpoint_id = 1
    requests_mock.get(
        "http://portainer.local:9000/api/endpoints/2/docker/containers/json?all=true",
        json=[{"Id": "abc"}],
    )

    response = client.post(f"/endpoints/{endpoint_id}/test")

    assert "OK - 1 container(s) found" in response.text


def test_delete_endpoint_removes_it(client):
    client.post(
        "/endpoints",
        data={
            "name": "lab",
            "portainer_url": "http://portainer.local:9000/api",
            "api_key": "my-secret-key",
            "endpoint_id": "2",
        },
    )

    client.post("/endpoints/1/delete")
    response = client.get("/endpoints")

    assert "<td>lab</td>" not in response.text
