import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(db_path=None):
    db_path = db_path or os.getenv("SLEEPERSTACK_DB_PATH", "/data/sleeperstack.db")
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db(bind_engine=None):
    from app import models  # noqa: F401 registers models on Base

    Base.metadata.create_all(bind=bind_engine or engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
