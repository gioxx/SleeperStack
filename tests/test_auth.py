import pytest

from app.auth import (
    NotAuthenticated,
    bootstrap_admin,
    create_session_cookie_value,
    get_current_user,
    hash_password,
    read_session_cookie_value,
    verify_password,
)
from app.db import init_db, make_engine
from app.models import User
from sqlalchemy.orm import sessionmaker


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-value")


def make_session():
    engine = make_engine(db_path=":memory:")
    init_db(bind_engine=engine)
    return sessionmaker(bind=engine)()


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("correct-horse")

    assert hashed != "correct-horse"
    assert verify_password("correct-horse", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_session_cookie_roundtrip():
    value = create_session_cookie_value(42)

    assert read_session_cookie_value(value) == 42


def test_session_cookie_tampered_returns_none():
    value = create_session_cookie_value(42)
    tampered = value[:-1] + ("a" if value[-1] != "a" else "b")

    assert read_session_cookie_value(tampered) is None


def test_bootstrap_admin_creates_user_when_table_empty(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret-pass")
    session = make_session()

    bootstrap_admin(session)

    user = session.query(User).filter_by(username="admin").one()
    assert verify_password("s3cret-pass", user.password_hash)


def test_bootstrap_admin_requires_password_env(monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    session = make_session()

    with pytest.raises(RuntimeError):
        bootstrap_admin(session)


def test_bootstrap_admin_skips_when_users_exist(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret-pass")
    session = make_session()
    session.add(User(username="existing", password_hash="x", role="admin"))
    session.commit()

    bootstrap_admin(session)

    assert session.query(User).count() == 1


class FakeRequest:
    def __init__(self, cookies):
        self.cookies = cookies


def test_get_current_user_raises_when_no_cookie():
    session = make_session()

    with pytest.raises(NotAuthenticated):
        get_current_user(FakeRequest({}), session)


def test_get_current_user_returns_user_for_valid_cookie(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret-pass")
    session = make_session()
    bootstrap_admin(session)
    user = session.query(User).filter_by(username="admin").one()

    cookie_value = create_session_cookie_value(user.id)
    result = get_current_user(FakeRequest({"sleeperstack_session": cookie_value}), session)

    assert result.id == user.id
