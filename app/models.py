from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    portainer_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_id: Mapped[str] = mapped_column(String(50), nullable=False)

    rules: Mapped[list["Rule"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id"), nullable=False)
    target_label: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    endpoint: Mapped["Endpoint"] = relationship(back_populates="rules")


class RunHistory(Base):
    __tablename__ = "run_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("rules.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
