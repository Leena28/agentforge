import asyncio

from celery import Celery

from app.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "agentforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="workflow.execute")
def execute_workflow_task(run_id: str) -> dict[str, str]:
    from app.core.logging import logger
    from app.db.session import AsyncSessionLocal
    from app.runtime.langgraph_runtime import execute_workflow_run
    from app.channels.slack_delivery import deliver_run_result_if_needed

    async def _run() -> None:
        async with AsyncSessionLocal() as session:
            run = await execute_workflow_run(session, run_id)
            await deliver_run_result_if_needed(run)

    asyncio.run(_run())
    return {"run_id": run_id, "status": "finished"}


@celery_app.task(name="workflow.execute_scheduled")
def execute_scheduled_workflow_task(
    template_key: str,
    input_message: str,
    agent_id: str,
) -> dict[str, str]:
    from app.db.session import AsyncSessionLocal
    from app.services.run_service import create_run

    async def _run() -> None:
        async with AsyncSessionLocal() as session:
            run = await create_run(
                session,
                template_key=template_key,
                input_message=input_message,
                channel="scheduler",
                source_metadata={"agent_id": agent_id, "triggered_by": "celery_beat"},
            )
            from app.runtime.langgraph_runtime import execute_workflow_run
            from app.channels.slack_delivery import deliver_run_result_if_needed
            run = await execute_workflow_run(session, run.id)
            await deliver_run_result_if_needed(run)

    asyncio.run(_run())
    return {"template_key": template_key, "status": "finished"}