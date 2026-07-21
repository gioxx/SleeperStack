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
        yield test_client


def test_root_redirects_to_login_when_not_authenticated(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303

    dashboard_response = client.get("/dashboard", follow_redirects=False)
    assert dashboard_response.status_code == 303
    assert dashboard_response.headers["location"] == "/login"


def test_login_with_wrong_password_shows_error(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert "Invalid username or password" in response.text


def test_login_with_correct_password_sets_cookie_and_allows_dashboard(client):
    response = client.post(
        "/login", data={"username": "admin", "password": "s3cret-pass"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "sleeperstack_session" in response.cookies

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200
    assert "Logged in as admin" in dashboard_response.text


def test_logout_clears_session(client):
    client.post("/login", data={"username": "admin", "password": "s3cret-pass"})
    client.post("/logout")

    dashboard_response = client.get("/dashboard", follow_redirects=False)
    assert dashboard_response.status_code == 303
    assert dashboard_response.headers["location"] == "/login"
