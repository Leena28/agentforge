import asyncio

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from app.config.settings import get_settings
from app.core.logging import configure_logging, logger


settings = get_settings()

app = AsyncApp(
    token=settings.slack_bot_token or "xoxb-placeholder",
    signing_secret=settings.slack_signing_secret or "placeholder",
)


async def _start_slack_run(text: str, metadata: dict[str, str]) -> str:
    from app.db.session import AsyncSessionLocal
    from app.services.run_service import create_run
    from app.workers.celery_app import execute_workflow_task
    from app.services.template_service import get_template
    from app.runtime.langgraph_runtime import execute_workflow_run

    async with AsyncSessionLocal() as session:
        template = await get_template(session, settings.slack_default_template)
        if not template:
            raise ValueError(
                f"Default template not found: {settings.slack_default_template}"
            )
        run = await create_run(
            session,
            template_key=template.key,
            input_message=text,
            channel="slack",
            source_metadata=metadata,
        )
        #execute_workflow_task.delay(run.id)
        await execute_workflow_run(session, run.id)
        logger.info(
            "slack_run_started",
            run_id=run.id,
            template=template.key,
        )
        return run.id


@app.event("app_mention")
async def handle_app_mention(event, say):
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts", "")
    try:
        run_id = await _start_slack_run(
            text,
            {
                "channel": event.get("channel", ""),
                "thread_ts": thread_ts,
                "user": event.get("user", ""),
                "event_type": "app_mention",
            },
        )
        await say(
            text=(
                f"Got it. Starting workflow `{run_id}`.\n"
                f"I will post the result here when done."
            ),
            thread_ts=thread_ts,
        )
    except Exception as exc:
        logger.warning("slack_mention_failed", error=str(exc))
        await say(
            text="Sorry, I could not start the workflow. Please try again.",
            thread_ts=thread_ts,
        )


@app.message("")
async def handle_dm(message, say):
    if message.get("channel_type") != "im" or message.get("bot_id"):
        return
    text = message.get("text", "")
    thread_ts = message.get("thread_ts") or message.get("ts", "")
    try:
        run_id = await _start_slack_run(
            text,
            {
                "channel": message.get("channel", ""),
                "thread_ts": thread_ts,
                "user": message.get("user", ""),
                "event_type": "direct_message",
            },
        )
        await say(
            f"Workflow `{run_id}` started. "
            f"I will post the result in this thread when done."
        )
    except Exception as exc:
        logger.warning("slack_dm_failed", error=str(exc))
        await say("Sorry, I could not start the workflow. Please try again.")


async def main() -> None:
    configure_logging()
    if not settings.slack_bot_token or not settings.slack_app_token:
        logger.warning(
            "slack_not_configured",
            message="SLACK_BOT_TOKEN or SLACK_APP_TOKEN not set. Slack bot will not start.",
        )
        return
    handler = AsyncSocketModeHandler(app, settings.slack_app_token)
    logger.info("slack_bot_starting")
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())