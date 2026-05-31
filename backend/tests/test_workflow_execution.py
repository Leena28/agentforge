import pytest
from app.db.session import AsyncSessionLocal
from app.services.run_service import create_run, get_run
from app.runtime.langgraph_runtime import execute_workflow_run


@pytest.mark.asyncio
async def test_chargeback_workflow_creates_events_messages_tools():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message=(
                "Chargeback received for transaction TXN-4821 "
                "from merchant Rappi Brazil. Customer claims "
                "they did not authorise the BRL 350 charge."
            ),
            channel="web",
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    assert detail is not None
    assert detail.status in {"awaiting_approval", "completed"}
    assert detail.final_response is not None
    assert len(detail.messages) >= 2
    assert len(detail.events) >= 4
    assert {t.tool_name for t in detail.tool_calls} >= {
        "transaction_lookup",
        "fraud_risk_scorer",
    }


@pytest.mark.asyncio
async def test_chargeback_high_risk_requires_approval():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message=(
                "Chargeback received for TXN-9034 from iFood Brazil. "
                "Fraudulent transaction with duplicate auth detected."
            ),
            channel="web",
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    assert detail is not None
    assert detail.status == "awaiting_approval"
    assert detail.confidence is not None


@pytest.mark.asyncio
async def test_smart_routing_workflow_completes():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-smart-routing",
            input_message=(
                "Find best payment route for merchant iFood Brazil. "
                "Transaction amount BRL 420, card payment."
            ),
            channel="web",
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    assert detail is not None
    assert detail.status == "completed"
    assert detail.final_response is not None
    assert len(detail.messages) >= 2
    assert len(detail.events) >= 4
    assert {t.tool_name for t in detail.tool_calls} >= {
        "provider_health_check",
        "fee_calculator",
        "route_recommendation",
    }


@pytest.mark.asyncio
async def test_approval_flow_completes_run():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message=(
                "Chargeback received for TXN-9034 from iFood Brazil. "
                "Fraudulent transaction."
            ),
            channel="web",
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)
        assert detail.status == "awaiting_approval"

        from app.services.run_service import add_event, add_message, set_run_status
        await add_event(
            session,
            run_id=detail.id,
            event_type="approval_accepted",
            title="Human approval accepted",
            body="Approved in test.",
            node_id="approval-gate",
        )
        await add_message(
            session,
            run_id=detail.id,
            sender="Human Approver",
            recipient="Merchant",
            channel="web",
            content=detail.final_response or "Approved.",
        )
        await set_run_status(session, detail, "completed")
        await session.commit()

    async with AsyncSessionLocal() as session:
        approved = await get_run(session, run_id)

    assert approved.status == "completed"
    assert any(
        e.event_type == "approval_accepted"
        for e in approved.events
    )