import pytest
from app.db.session import AsyncSessionLocal
from app.services.agent_service import (
    create_agent,
    get_agent,
    list_agents,
    update_agent,
    delete_agent,
    get_agents_by_node_binding,
)
from app.schemas.agents import AgentCreate, AgentUpdate


@pytest.mark.asyncio
async def test_agent_creation_persists_all_fields():
    payload = AgentCreate(
        name="Chargeback Investigator",
        role="Investigates chargeback disputes for Yuno merchants",
        system_prompt=(
            "You investigate chargeback disputes and produce "
            "audit-ready summaries for Yuno operators."
        ),
        model="gpt-4o-mini",
        tools=["transaction_lookup", "fraud_risk_scorer"],
        channels=["web", "slack"],
        schedules={"mode": "daily", "hour": 9},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 8, "max_cost_usd": 0.10},
        skills=["chargeback_classification", "fraud_detection"],
        interaction_rules=["Always cite transaction ID"],
        guardrails=["No refund without approval"],
        runtime_node_binding="triage_agent",
    )
    async with AsyncSessionLocal() as session:
        agent = await create_agent(session, payload)

    assert agent.id is not None
    assert agent.name == "Chargeback Investigator"
    assert agent.model == "gpt-4o-mini"
    assert agent.tools == ["transaction_lookup", "fraud_risk_scorer"]
    assert agent.channels == ["web", "slack"]
    assert agent.schedules == {"mode": "daily", "hour": 9}
    assert agent.memory == {"type": "postgres_pgvector", "enabled": True}
    assert agent.limits == {"max_steps": 8, "max_cost_usd": 0.10}
    assert agent.skills == ["chargeback_classification", "fraud_detection"]
    assert agent.interaction_rules == ["Always cite transaction ID"]
    assert agent.guardrails == ["No refund without approval"]
    assert agent.runtime_node_binding == "triage_agent"
    assert agent.created_at is not None
    assert agent.updated_at is not None


@pytest.mark.asyncio
async def test_agent_list_returns_all_agents():
    async with AsyncSessionLocal() as session:
        agents = await list_agents(session)
    assert len(agents) >= 5


@pytest.mark.asyncio
async def test_agent_get_by_id():
    async with AsyncSessionLocal() as session:
        agents = await list_agents(session)
        first = agents[0]
        fetched = await get_agent(session, first.id)
    assert fetched is not None
    assert fetched.id == first.id
    assert fetched.name == first.name


@pytest.mark.asyncio
async def test_agent_update_partial():
    async with AsyncSessionLocal() as session:
        agents = await list_agents(session)
        agent = agents[0]
        original_name = agent.name
        updated = await update_agent(
            session,
            agent,
            AgentUpdate(name="Updated Agent Name"),
        )
    assert updated.name == "Updated Agent Name"
    assert updated.name != original_name


@pytest.mark.asyncio
async def test_agent_delete():
    payload = AgentCreate(
        name="Temp Agent",
        role="Temporary test agent",
        system_prompt="You are a temporary test agent for deletion testing.",
        model="gpt-4o-mini",
    )
    async with AsyncSessionLocal() as session:
        agent = await create_agent(session, payload)
        agent_id = agent.id
        await delete_agent(session, agent)
        deleted = await get_agent(session, agent_id)
    assert deleted is None


@pytest.mark.asyncio
async def test_get_agents_by_node_binding():
    async with AsyncSessionLocal() as session:
        bindings = await get_agents_by_node_binding(session)
    assert "triage_agent" in bindings
    assert "resolution_agent" in bindings
    assert "routing_agent" in bindings
    assert bindings["triage_agent"].system_prompt is not None
    assert bindings["triage_agent"].model is not None