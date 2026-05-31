import asyncio

from app.db.session import AsyncSessionLocal, init_db
from app.services.agent_service import create_agent, list_agents
from app.services.template_service import upsert_template
from app.schemas.agents import AgentCreate


CHARGEBACK_GRAPH = {
    "nodes": [
        {"id": "slack-intake", "type": "channel", "label": "Slack Intake", "x": 60, "y": 160},
        {"id": "triage-agent", "type": "agent", "label": "Chargeback Triage Agent", "x": 300, "y": 160},
        {"id": "fraud-risk-tool", "type": "tool", "label": "Fraud Risk Scorer", "x": 560, "y": 80},
        {"id": "transaction-tool", "type": "tool", "label": "Transaction Lookup", "x": 560, "y": 240},
        {"id": "resolution-agent", "type": "agent", "label": "Resolution Agent", "x": 820, "y": 160},
        {"id": "approval-gate", "type": "approval", "label": "Human Approval Gate", "x": 1080, "y": 160},
    ],
    "edges": [
        {"source": "slack-intake", "target": "triage-agent", "label": "chargeback message"},
        {"source": "triage-agent", "target": "fraud-risk-tool", "label": "score fraud risk"},
        {"source": "triage-agent", "target": "transaction-tool", "label": "lookup transaction"},
        {"source": "fraud-risk-tool", "target": "resolution-agent", "label": "risk context"},
        {"source": "transaction-tool", "target": "resolution-agent", "label": "transaction context"},
        {"source": "resolution-agent", "target": "approval-gate", "label": "if high risk"},
        {"source": "approval-gate", "target": "resolution-agent", "label": "feedback loop"},
    ],
}

SMART_ROUTING_GRAPH = {
    "nodes": [
        {"id": "slack-intake", "type": "channel", "label": "Slack Intake", "x": 60, "y": 160},
        {"id": "routing-agent", "type": "agent", "label": "Routing Strategy Agent", "x": 300, "y": 160},
        {"id": "provider-health-tool", "type": "tool", "label": "Provider Health Check", "x": 560, "y": 80},
        {"id": "fee-calculator-tool", "type": "tool", "label": "Fee and FX Calculator", "x": 560, "y": 240},
        {"id": "risk-agent", "type": "agent", "label": "Risk Conditions Agent", "x": 820, "y": 160},
        {"id": "policy-agent", "type": "agent", "label": "Compliance Policy Agent", "x": 1080, "y": 160},
        {"id": "recommendation", "type": "output", "label": "Route Recommendation", "x": 1340, "y": 160},
    ],
    "edges": [
        {"source": "slack-intake", "target": "routing-agent", "label": "payment context"},
        {"source": "routing-agent", "target": "provider-health-tool", "label": "check availability"},
        {"source": "routing-agent", "target": "fee-calculator-tool", "label": "calculate fees"},
        {"source": "provider-health-tool", "target": "risk-agent", "label": "health data"},
        {"source": "fee-calculator-tool", "target": "risk-agent", "label": "cost data"},
        {"source": "risk-agent", "target": "policy-agent", "label": "risk assessment"},
        {"source": "policy-agent", "target": "recommendation", "label": "approved route"},
    ],
}

BUILTIN_TEMPLATES = [
    {
        "key": "yuno-chargeback-management",
        "name": "Yuno Chargeback Management",
        "description": (
            "Triages an incoming chargeback dispute, looks up the original transaction, "
            "scores fraud risk, and drafts a resolution response. Routes high risk cases "
            "to a human approval gate before sending the final response."
        ),
        "category": "yuno-protect",
        "graph": CHARGEBACK_GRAPH,
        "default_input": (
            "Chargeback received for transaction TXN-4821 from merchant Rappi Brazil. "
            "Customer claims they did not authorise the BRL 350 charge on 24 May 2026."
        ),
        "is_builtin": True,
    },
    {
        "key": "yuno-smart-routing",
        "name": "Yuno Smart Payment Routing",
        "description": (
            "Analyses provider health, transaction fees, FX spreads, and risk conditions "
            "to recommend the optimal payment route for a merchant transaction. "
            "Produces a ranked provider recommendation with full reasoning."
        ),
        "category": "yuno-optimize",
        "graph": SMART_ROUTING_GRAPH,
        "default_input": (
            "Find the best payment route for merchant iFood Brazil. "
            "Transaction amount BRL 420, card payment, customer in Sao Paulo."
        ),
        "is_builtin": True,
    },
]

DEMO_AGENTS = [
    AgentCreate(
        name="Chargeback Triage Agent",
        role="Classifies incoming chargeback disputes and determines fraud risk level.",
        system_prompt=(
            "You are a chargeback triage specialist for Yuno. "
            "Your job is to classify incoming chargeback disputes, look up the original "
            "transaction details, and determine whether the chargeback is likely genuine fraud, "
            "merchant error, or friendly fraud. Always cite the transaction ID and merchant name. "
            "Hand off high risk cases to the resolution agent with a clear risk summary. "
            "Never promise a refund or reversal without approval."
        ),
        model="gpt-4o-mini",
        tools=["transaction_lookup", "fraud_risk_scorer"],
        channels=["slack", "web"],
        schedules={"mode": "on_demand"},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 8, "max_cost_usd": 0.10},
        skills=["chargeback_classification", "fraud_detection", "payment_ops"],
        interaction_rules=[
            "Always cite transaction ID",
            "Never promise refund without approval",
            "Escalate high fraud signals immediately",
        ],
        guardrails=[
            "No irreversible action without human approval",
            "No customer PII in logs",
        ],
        runtime_node_binding="triage_agent",
    ),
    AgentCreate(
        name="Resolution Agent",
        role="Drafts chargeback resolution responses and operator recommendations.",
        system_prompt=(
            "You are a payment resolution specialist for Yuno. "
            "You write clear, concise chargeback resolution responses for merchants and operators. "
            "Be transparent about the risk assessment and evidence. "
            "Never commit to a refund or reversal before human approval is granted. "
            "Keep responses professional and auditable."
        ),
        model="gpt-4o-mini",
        tools=["draft_response"],
        channels=["slack", "web"],
        schedules={"mode": "on_demand"},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 6, "max_cost_usd": 0.08},
        skills=["resolution_drafting", "customer_communication", "summarisation"],
        interaction_rules=[
            "Use plain professional language",
            "Always state approval status clearly",
            "No confidential provider details in customer text",
        ],
        guardrails=[
            "No refund commitment without approval",
            "No customer PII in response",
        ],
        runtime_node_binding="resolution_agent",
    ),
    AgentCreate(
        name="Routing Strategy Agent",
        role="Analyses provider health and fees to recommend the optimal payment route.",
        system_prompt=(
            "You are a payment routing strategist for Yuno. "
            "Your job is to analyse available payment providers, their current health status, "
            "transaction fees, FX spreads, and country-specific risk conditions. "
            "Recommend the best provider for each transaction with clear reasoning. "
            "Always include success rate, estimated cost, and any active incidents in your recommendation."
        ),
        model="gpt-4o-mini",
        tools=["provider_health_check", "fee_calculator"],
        channels=["slack", "web"],
        schedules={"mode": "on_demand"},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 8, "max_cost_usd": 0.10},
        skills=["routing_strategy", "provider_analysis", "cost_optimisation"],
        interaction_rules=[
            "Always include success rate in recommendation",
            "Flag active provider incidents",
            "Show top 3 candidates with scores",
        ],
        guardrails=[
            "Never recommend a provider with active critical incident",
            "Always include fallback provider",
        ],
        runtime_node_binding="routing_agent",
    ),
    AgentCreate(
        name="Risk Conditions Agent",
        role="Evaluates transaction risk against Yuno risk conditions and 3DS requirements.",
        system_prompt=(
            "You are a risk conditions analyst for Yuno. "
            "You evaluate payment transactions against defined risk conditions, "
            "3DS authentication requirements, and country-specific compliance rules. "
            "Produce a clear risk assessment with confidence score and recommended action. "
            "Flag any transactions that require 3DS or additional verification."
        ),
        model="gpt-4o-mini",
        tools=["risk_conditions_check", "three_ds_checker"],
        channels=["agent"],
        schedules={"mode": "on_demand"},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 6, "max_cost_usd": 0.08},
        skills=["risk_assessment", "compliance_check", "3ds_evaluation"],
        interaction_rules=[
            "Always include confidence score",
            "Flag 3DS requirements explicitly",
            "Cite specific risk condition violated",
        ],
        guardrails=[
            "Never bypass 3DS requirement",
            "Escalate critical risk flags",
        ],
        runtime_node_binding="risk_agent",
    ),
    AgentCreate(
        name="Compliance Policy Agent",
        role="Reviews routing recommendations against Yuno compliance policies.",
        system_prompt=(
            "You are a compliance policy reviewer for Yuno. "
            "You review payment routing recommendations against Yuno's compliance policies, "
            "regulatory requirements, and merchant agreements. "
            "Approve or reject routing recommendations with clear policy reasoning. "
            "Produce a final operator decision that is auditable and defensible."
        ),
        model="gpt-4o-mini",
        tools=["policy_checker"],
        channels=["agent"],
        schedules={"mode": "on_demand"},
        memory={"type": "postgres_pgvector", "enabled": True},
        limits={"max_steps": 6, "max_cost_usd": 0.08},
        skills=["compliance_review", "policy_enforcement", "audit_trail"],
        interaction_rules=[
            "Always cite policy basis for decision",
            "Produce auditable reasoning",
            "Flag regulatory concerns explicitly",
        ],
        guardrails=[
            "Never approve non-compliant routes",
            "Always include policy reference",
        ],
        runtime_node_binding="policy_agent",
    ),
]


async def seed() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        for template in BUILTIN_TEMPLATES:
            await upsert_template(session, **template)

        existing_agents = await list_agents(session)
        if not existing_agents:
            for agent in DEMO_AGENTS:
                await create_agent(session, agent)


if __name__ == "__main__":
    asyncio.run(seed())