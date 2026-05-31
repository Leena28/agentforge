from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.templates import (
    WorkflowTemplateCreate,
    WorkflowTemplateRead,
    WorkflowTemplateUpdate,
)
from app.services.template_service import (
    create_template,
    get_template,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[WorkflowTemplateRead])
async def list_templates_route(
    session: AsyncSession = Depends(get_session),
):
    return await list_templates(session)


@router.get("/{template_key}", response_model=WorkflowTemplateRead)
async def get_template_route(
    template_key: str,
    session: AsyncSession = Depends(get_session),
):
    template = await get_template(session, template_key)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("", response_model=WorkflowTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template_route(
    payload: WorkflowTemplateCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await create_template(session, payload)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Template key already exists")


@router.patch("/{template_key}", response_model=WorkflowTemplateRead)
async def update_template_route(
    template_key: str,
    payload: WorkflowTemplateUpdate,
    session: AsyncSession = Depends(get_session),
):
    template = await get_template(session, template_key)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_builtin:
        raise HTTPException(
            status_code=400,
            detail="Built-in templates cannot be edited"
        )
    return await update_template(session, template, payload)