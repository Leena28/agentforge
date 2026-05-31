from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    # run identity
    run_id: str
    template_key: str
    user_message: str

    # chargeback workflow fields
    transaction_id: str
    merchant_id: str
    merchant_name: str
    country: str
    currency: str
    amount: float
    transaction: dict[str, Any]
    fraud_risk: dict[str, Any]
    chargeback_reason: str

    # smart routing workflow fields
    provider: str
    provider_health: dict[str, Any]
    fee_data: dict[str, Any]
    risk_assessment: dict[str, Any]
    route_recommendation: dict[str, Any]

    # shared output fields
    final_response: str
    confidence: float
    needs_approval: bool
    token_count: int
    estimated_cost_usd: float

    # agent configs loaded from DB
    agent_configs: dict[str, Any]

    # message and event tracking
    messages: list[dict[str, Any]]
    events: list[dict[str, Any]]