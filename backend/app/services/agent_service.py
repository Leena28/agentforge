from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agents import Agent
from app.db.base import new_id
from app.schemas.agents import AgentCreate, AgentUpdate


async def list_agents(session: AsyncSession) -> Sequence[Agent]:
    result = await session.execute(
        select(Agent).order_by(Agent.created_at)
    )
    return result.scalars().all()


async def get_agent(session: AsyncSession, agent_id: str) -> Agent | None:
    return await session.get(Agent, agent_id)


async def create_agent(session: AsyncSession, payload: AgentCreate) -> Agent:
    agent = Agent(**payload.model_dump())
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


async def update_agent(
    session: AsyncSession,
    agent: Agent,
    payload: AgentUpdate,
) -> Agent:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    agent.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(agent)
    return agent


async def delete_agent(session: AsyncSession, agent: Agent) -> None:
    await session.delete(agent)
    await session.commit()


async def get_agents_by_node_binding(
    session: AsyncSession,
) -> dict[str, Agent]:
    result = await session.execute(
        select(Agent).where(Agent.runtime_node_binding.isnot(None))
    )
    agents = result.scalars().all()
    return {
        agent.runtime_node_binding: agent
        for agent in agents
        if agent.runtime_node_binding
    }