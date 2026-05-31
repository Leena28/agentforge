from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=160)
    system_prompt: str = Field(min_length=10)
    model: str = Field(default="gpt-4o-mini")
    tools: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    schedules: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, Any] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    interaction_rules: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    runtime_node_binding: str | None = Field(default=None)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    channels: list[str] | None = None
    schedules: dict[str, Any] | None = None
    memory: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None
    skills: list[str] | None = None
    interaction_rules: list[str] | None = None
    guardrails: list[str] | None = None
    runtime_node_binding: str | None = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime