from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowNodeSchema(BaseModel):
    id: str
    type: str
    label: str
    x: float
    y: float


class WorkflowEdgeSchema(BaseModel):
    source: str
    target: str
    label: str = Field(default="")


class WorkflowGraphSchema(BaseModel):
    nodes: list[WorkflowNodeSchema] = Field(default_factory=list)
    edges: list[WorkflowEdgeSchema] = Field(default_factory=list)


class WorkflowTemplateBase(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10)
    category: str = Field(default="custom")
    graph: WorkflowGraphSchema
    default_input: str = Field(min_length=3)


class WorkflowTemplateCreate(WorkflowTemplateBase):
    key: str = Field(min_length=3, max_length=120)


class WorkflowTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    graph: WorkflowGraphSchema | None = None
    default_input: str | None = None


class WorkflowTemplateRead(WorkflowTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    is_builtin: bool
    created_at: datetime
    updated_at: datetime