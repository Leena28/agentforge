from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.templates import WorkflowTemplate
from app.schemas.templates import WorkflowTemplateCreate, WorkflowTemplateUpdate


async def list_templates(session: AsyncSession) -> Sequence[WorkflowTemplate]:
    result = await session.execute(
        select(WorkflowTemplate).order_by(WorkflowTemplate.name)
    )
    return result.scalars().all()


async def get_template(
    session: AsyncSession,
    key: str,
) -> WorkflowTemplate | None:
    result = await session.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.key == key)
    )
    return result.scalar_one_or_none()


async def create_template(
    session: AsyncSession,
    payload: WorkflowTemplateCreate,
) -> WorkflowTemplate:
    data = payload.model_dump()
    data["graph"] = data["graph"].model_dump() if hasattr(data["graph"], "model_dump") else data["graph"]
    template = WorkflowTemplate(**data, is_builtin=False)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def update_template(
    session: AsyncSession,
    template: WorkflowTemplate,
    payload: WorkflowTemplateUpdate,
) -> WorkflowTemplate:
    data = payload.model_dump(exclude_unset=True)
    if "graph" in data and hasattr(data["graph"], "model_dump"):
        data["graph"] = data["graph"].model_dump()
    for key, value in data.items():
        setattr(template, key, value)
    await session.commit()
    await session.refresh(template)
    return template


async def upsert_template(
    session: AsyncSession,
    key: str,
    name: str,
    description: str,
    graph: dict[str, Any],
    default_input: str,
    category: str = "payments",
    is_builtin: bool = True,
) -> WorkflowTemplate:
    existing = await get_template(session, key)
    if existing:
        existing.name = name
        existing.description = description
        existing.graph = graph
        existing.default_input = default_input
        existing.category = category
        await session.commit()
        await session.refresh(existing)
        return existing
    template = WorkflowTemplate(
        key=key,
        name=name,
        description=description,
        graph=graph,
        default_input=default_input,
        category=category,
        is_builtin=is_builtin,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template