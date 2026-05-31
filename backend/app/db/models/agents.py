from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, new_id, utcnow


JsonType = JSON().with_variant(JSONB, "postgresql")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_id
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(160), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    tools: Mapped[list[str]] = mapped_column(JsonType, default=list)
    channels: Mapped[list[str]] = mapped_column(JsonType, default=list)
    schedules: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    memory: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    limits: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    skills: Mapped[list[str]] = mapped_column(JsonType, default=list)
    interaction_rules: Mapped[list[str]] = mapped_column(JsonType, default=list)
    guardrails: Mapped[list[str]] = mapped_column(JsonType, default=list)
    runtime_node_binding: Mapped[str | None] = mapped_column(
        String(120), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )