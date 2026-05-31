from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.models.agents import Agent
from app.schemas.agents import AgentCreate, AgentRead, AgentUpdate
from app.services.agent_service import (
    create_agent,
    delete_agent,
    get_agent,
    list_agents,
    update_agent,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
async def list_agents_route(
    session: AsyncSession = Depends(get_session),
):
    return await list_agents(session)


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent_route(
    payload: AgentCreate,
    session: AsyncSession = Depends(get_session),
):
    return await create_agent(session, payload)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent_route(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent_route(
    agent_id: str,
    payload: AgentUpdate,
    session: AsyncSession = Depends(get_session),
):
    agent = await get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await update_agent(session, agent, payload)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_route(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await delete_agent(session, agent)