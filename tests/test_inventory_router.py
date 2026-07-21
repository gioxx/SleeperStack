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


def test_inventory_lists_all_containers_including_unlabeled(client, requests_mock):
    requests_mock.get(
        "http://portainer.local:9000/api/endpoints/2/docker/containers/json?all=true",
        json=[
            {
                "Id": "abc",
                "Names": ["/night-app"],
                "State": "running",
                "Status": "Up 3 days",
                "Image": "myapp:latest",
                "Created": 1700000000,
                "Labels": {"autoshutdown": "night", "com.docker.compose.project": "stackone"},
                "Ports": [{"PrivatePort": 80, "PublicPort": 8080, "Type": "tcp"}],
                "NetworkSettings": {"Networks": {"bridge": {"IPAddress": "172.17.0.2"}}},
            },
            {
                "Id": "def",
                "Names": ["/plain-app"],
                "State": "exited",
                "Status": "Exited (0) 2 hours ago",
                "Image": "other:latest",
                "Created": 1700000000,
                "Labels": {},
                "Ports": [],
                "NetworkSettings": {"Networks": {}},
            },
        ],
    )

    response = client.get("/inventory")

    assert "night-app" in response.text
    assert "stackone" in response.text
    assert "8080-&gt;80/tcp" in response.text
    assert "172.17.0.2" in response.text
    assert "plain-app" in response.text


def test_inventory_shows_connection_error(client, requests_mock):
    requests_mock.get(
        "http://portainer.local:9000/api/endpoints/2/docker/containers/json?all=true",
        status_code=401,
        text="unauthorized",
    )

    response = client.get("/inventory")

    assert "Connection error" in response.text
