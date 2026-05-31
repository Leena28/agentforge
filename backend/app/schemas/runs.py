from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    sender: str
    recipient: str
    channel: str
    content: str
    payload: dict[str, Any]
    created_at: datetime


class RunEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    event_type: str
    title: str
    body: str
    node_id: str | None
    payload: dict[str, Any]
    token_count: int
    cost_usd: float
    created_at: datetime


class ToolExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    tool_name: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any]
    duration_ms: int
    created_at: datetime


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_key: str
    status: str
    channel: str
    input_message: str
    final_response: str | None
    token_count: int
    estimated_cost_usd: float
    confidence: float | None
    source_metadata: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class WorkflowRunDetail(WorkflowRunRead):
    messages: list[AgentMessageRead] = Field(default_factory=list)
    events: list[RunEventRead] = Field(default_factory=list)
    tool_calls: list[ToolExecutionRead] = Field(default_factory=list)


class StartRunRequest(BaseModel):
    template_key: str = Field(min_length=3, max_length=120)
    input_message: str = Field(min_length=3)
    channel: str = Field(default="web")
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class StartRunResponse(BaseModel):
    run_id: str
    status: str


class ApproveRunRequest(BaseModel):
    approved_by: str = Field(default="operator")
    notes: str | None = None


class MetricsRead(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    active_agents: int
    total_messages: int
    total_tokens: int
    estimated_cost_usd: float