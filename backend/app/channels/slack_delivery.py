from app.db.models.runs import WorkflowRun
from app.config.settings import get_settings
from app.core.logging import logger

try:
    from slack_sdk.web.async_client import AsyncWebClient
except ImportError:
    AsyncWebClient = None


async def deliver_run_result_if_needed(run: WorkflowRun) -> None:
    settings = get_settings()

    if run.channel != "slack" or not settings.slack_bot_token:
        return

    channel = run.source_metadata.get("channel")
    thread_ts = run.source_metadata.get("thread_ts")

    if not channel:
        logger.warning(
            "slack_delivery_missing_channel",
            run_id=run.id,
        )
        return

    if run.status == "awaiting_approval":
        text = (
            f"Workflow `{run.id}` is waiting for human approval.\n\n"
            f"Draft response:\n{run.final_response or 'No draft generated.'}"
        )
    elif run.status == "completed":
        text = (
            f"Workflow `{run.id}` completed.\n\n"
            f"{run.final_response or 'Done.'}"
        )
    else:
        text = (
            f"Workflow `{run.id}` ended with status `{run.status}`.\n\n"
            f"{run.final_response or ''}"
        )

    if AsyncWebClient is None:
        logger.warning("slack_sdk_not_installed", run_id=run.id)
        return

    try:
        client = AsyncWebClient(token=settings.slack_bot_token)
        await client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts or None,
        )
        logger.info(
            "slack_delivery_sent",
            run_id=run.id,
            channel=channel,
        )
    except Exception as exc:
        logger.warning(
            "slack_delivery_failed",
            run_id=run.id,
            error=str(exc),
        )