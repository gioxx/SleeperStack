import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User

_hasher = PasswordHasher()
SESSION_COOKIE_NAME = "sleeperstack_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


class NotAuthenticated(Exception):
    pass


def hash_password(plain_password):
    return _hasher.hash(plain_password)


def verify_password(plain_password, password_hash):
    try:
        return _hasher.verify(password_hash, plain_password)
    except VerifyMismatchError:
        return False


def _get_serializer():
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is required in server mode")
    return URLSafeTimedSerializer(secret, salt="sleeperstack-session")


def create_session_cookie_value(user_id):
    return _get_serializer().dumps({"user_id": user_id})


def read_session_cookie_value(value):
    try:
        data = _get_serializer().loads(value, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    return data.get("user_id")


def bootstrap_admin(session: Session):
    if session.query(User).count() > 0:
        return

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required to bootstrap the first admin user"
        )

    session.add(User(username=username, password_hash=hash_password(password), role="admin"))
    session.commit()


def get_current_user(request: Request, db: Session = Depends(get_session)):
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_value:
        raise NotAuthenticated()

    user_id = read_session_cookie_value(cookie_value)
    if user_id is None:
        raise NotAuthenticated()

    user = db.get(User, user_id)
    if user is None:
        raise NotAuthenticated()

    return user
