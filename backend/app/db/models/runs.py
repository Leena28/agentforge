from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, new_id, utcnow


JsonType = JSON().with_variant(JSONB, "postgresql")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_id
    )
    template_key: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="queued", index=True
    )
    channel: Mapped[str] = mapped_column(
        String(40), nullable=False, default="web"
    )
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    final_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        JsonType, default=dict
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )
    events: Mapped[list["RunEvent"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunEvent.created_at",
    )
    tool_calls: Mapped[list["ToolExecution"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ToolExecution.created_at",
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_id
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    recipient: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    run: Mapped["WorkflowRun"] = relationship(back_populates="messages")


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_id
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    node_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    run: Mapped["WorkflowRun"] = relationship(back_populates="events")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_id
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="succeeded"
    )
    input: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    run: Mapped["WorkflowRun"] = relationship(back_populates="tool_calls")