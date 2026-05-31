import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.runs import AgentMessage, RunEvent, ToolExecution, WorkflowRun
from app.db.models.templates import WorkflowTemplate
from app.db.session import AsyncSessionLocal
from app.schemas.runs import ApproveRunRequest, StartRunRequest


async def list_runs(
    session: AsyncSession,
    limit: int = 20,
) -> Sequence[WorkflowRun]:
    result = await session.execute(
        select(WorkflowRun)
        .order_by(WorkflowRun.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_run(
    session: AsyncSession,
    run_id: str,
) -> WorkflowRun | None:
    result = await session.execute(
        select(WorkflowRun)
        .where(WorkflowRun.id == run_id)
        .options(
            selectinload(WorkflowRun.messages),
            selectinload(WorkflowRun.events),
            selectinload(WorkflowRun.tool_calls),
        )
    )
    return result.scalar_one_or_none()


async def create_run(
    session: AsyncSession,
    template_key: str,
    input_message: str,
    channel: str = "web",
    source_metadata: dict[str, Any] | None = None,
) -> WorkflowRun:
    run = WorkflowRun(
        template_key=template_key,
        input_message=input_message,
        channel=channel,
        source_metadata=source_metadata or {},
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def create_and_dispatch_run(
    session: AsyncSession,
    payload: StartRunRequest,
) -> dict[str, str]:
    from app.config.settings import get_settings
    settings = get_settings()

    template = await session.execute(
        select(WorkflowTemplate).where(
            WorkflowTemplate.key == payload.template_key
        )
    )
    template = template.scalar_one_or_none()
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")

    run = await create_run(
        session,
        template_key=payload.template_key,
        input_message=payload.input_message,
        channel=payload.channel,
        source_metadata=payload.source_metadata,
    )

    if settings.run_workflows_inline:
        from app.runtime.langgraph_runtime import execute_workflow_run
        await execute_workflow_run(session, run.id)
    else:
        from app.workers.celery_app import execute_workflow_task
        execute_workflow_task.delay(run.id)

    return {"run_id": run.id, "status": run.status}


async def approve_run(
    session: AsyncSession,
    run: WorkflowRun,
    payload: ApproveRunRequest,
) -> WorkflowRun:
    now = datetime.now(UTC)

    event = RunEvent(
        run_id=run.id,
        event_type="approval_accepted",
        title="Human approval accepted",
        body=payload.notes or f"Approved by {payload.approved_by}.",
        node_id="approval-gate",
        payload={
            "approved_by": payload.approved_by,
            "notes": payload.notes,
        },
    )
    session.add(event)

    message = AgentMessage(
        run_id=run.id,
        sender="Human Approver",
        recipient="Customer" if run.channel == "slack" else "Resolution Agent",
        channel=run.channel,
        content=run.final_response or "Approved.",
        payload={"approved_by": payload.approved_by},
    )
    session.add(message)

    run.status = "completed"
    run.completed_at = now

    await session.commit()

    from app.channels.slack_delivery import deliver_run_result_if_needed
    await deliver_run_result_if_needed(run)

    refreshed = await get_run(session, run.id)
    return refreshed


async def add_event(
    session: AsyncSession,
    run_id: str,
    event_type: str,
    title: str,
    body: str,
    node_id: str | None = None,
    payload: dict[str, Any] | None = None,
    token_count: int = 0,
    cost_usd: float = 0.0,
) -> RunEvent:
    event = RunEvent(
        run_id=run_id,
        event_type=event_type,
        title=title,
        body=body,
        node_id=node_id,
        payload=payload or {},
        token_count=token_count,
        cost_usd=cost_usd,
    )
    session.add(event)
    await session.flush()
    return event


async def add_message(
    session: AsyncSession,
    run_id: str,
    sender: str,
    recipient: str,
    channel: str,
    content: str,
    payload: dict[str, Any] | None = None,
) -> AgentMessage:
    message = AgentMessage(
        run_id=run_id,
        sender=sender,
        recipient=recipient,
        channel=channel,
        content=content,
        payload=payload or {},
    )
    session.add(message)
    await session.flush()
    return message


async def add_tool_execution(
    session: AsyncSession,
    run_id: str,
    tool_name: str,
    input: dict[str, Any],
    output: dict[str, Any],
    status: str = "succeeded",
    duration_ms: int = 0,
) -> ToolExecution:
    tool_call = ToolExecution(
        run_id=run_id,
        tool_name=tool_name,
        input=input,
        output=output,
        status=status,
        duration_ms=duration_ms,
    )
    session.add(tool_call)
    await session.flush()
    return tool_call


async def set_run_status(
    session: AsyncSession,
    run: WorkflowRun,
    status: str,
    final_response: str | None = None,
    confidence: float | None = None,
    token_count: int | None = None,
    estimated_cost_usd: float | None = None,
) -> WorkflowRun:
    now = datetime.now(UTC)
    run.status = status
    if status == "running" and run.started_at is None:
        run.started_at = now
    if status in {"completed", "failed"}:
        run.completed_at = now
    if final_response is not None:
        run.final_response = final_response
    if confidence is not None:
        run.confidence = confidence
    if token_count is not None:
        run.token_count = token_count
    if estimated_cost_usd is not None:
        run.estimated_cost_usd = estimated_cost_usd
    await session.flush()
    return run


async def metrics(session: AsyncSession) -> dict[str, Any]:
    from sqlalchemy import func
    from app.db.models.agents import Agent

    async def scalar(stmt: Any) -> Any:
        return (await session.execute(stmt)).scalar() or 0

    total_runs = await scalar(select(func.count(WorkflowRun.id)))
    completed_runs = await scalar(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "completed")
    )
    failed_runs = await scalar(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "failed")
    )
    active_agents = await scalar(select(func.count(Agent.id)))
    total_messages = await scalar(select(func.count(AgentMessage.id)))
    total_tokens = await scalar(
        select(func.coalesce(func.sum(WorkflowRun.token_count), 0))
    )
    estimated_cost_usd = await scalar(
        select(func.coalesce(func.sum(WorkflowRun.estimated_cost_usd), 0.0))
    )
    return {
        "total_runs": int(total_runs),
        "completed_runs": int(completed_runs),
        "failed_runs": int(failed_runs),
        "active_agents": int(active_agents),
        "total_messages": int(total_messages),
        "total_tokens": int(total_tokens),
        "estimated_cost_usd": float(estimated_cost_usd),
    }


async def stream_run_events(run_id: str) -> AsyncGenerator[str, None]:
    seen: set[str] = set()
    while True:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkflowRun).where(WorkflowRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                yield "event: error\ndata: {\"message\": \"run not found\"}\n\n"
                return

            events_result = await session.execute(
                select(RunEvent)
                .where(RunEvent.run_id == run_id)
                .order_by(RunEvent.created_at)
            )
            events = events_result.scalars().all()

            for event in events:
                if event.id in seen:
                    continue
                seen.add(event.id)
                data = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "title": event.title,
                    "body": event.body,
                    "node_id": event.node_id,
                    "token_count": event.token_count,
                    "cost_usd": event.cost_usd,
                    "created_at": event.created_at.isoformat(),
                }
                yield f"event: run_event\ndata: {json.dumps(data)}\n\n"

            if run.status in {"completed", "failed", "awaiting_approval"}:
                yield f"event: run_status\ndata: {json.dumps({'status': run.status})}\n\n"
                return

        await asyncio.sleep(1)