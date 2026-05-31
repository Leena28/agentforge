import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.db.session import AsyncSessionLocal
from app.services.run_service import create_run, get_run
from app.runtime.langgraph_runtime import execute_workflow_run
from app.channels.slack_delivery import deliver_run_result_if_needed


@pytest.mark.asyncio
async def test_slack_delivery_skipped_for_web_channel():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message="Chargeback received for TXN-4821 from Rappi Brazil.",
            channel="web",
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    with patch("app.channels.slack_delivery.get_settings") as mock_settings:
        mock_settings.return_value.slack_bot_token = "xoxb-test-token"
        with patch(
            "app.channels.slack_delivery.AsyncWebClient",
            new_callable=MagicMock,
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_client_class.return_value = mock_client
            await deliver_run_result_if_needed(detail)
            mock_client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_slack_delivery_skipped_when_no_token():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message="Chargeback received for TXN-4821 from Rappi Brazil.",
            channel="slack",
            source_metadata={
                "channel": "C012AB3CD",
                "thread_ts": "1234567890.123456",
            },
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    with patch("app.channels.slack_delivery.get_settings") as mock_settings:
        mock_settings.return_value.slack_bot_token = None
        with patch(
            "app.channels.slack_delivery.AsyncWebClient",
            new_callable=MagicMock,
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_client_class.return_value = mock_client
            await deliver_run_result_if_needed(detail)
            mock_client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_slack_delivery_sends_message_for_slack_channel():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message="Chargeback received for TXN-4821 from Rappi Brazil.",
            channel="slack",
            source_metadata={
                "channel": "C012AB3CD",
                "thread_ts": "1234567890.123456",
            },
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)

    with patch("app.channels.slack_delivery.get_settings") as mock_settings:
        mock_settings.return_value.slack_bot_token = "xoxb-test-token"
        with patch(
            "app.channels.slack_delivery.AsyncWebClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_client_class.return_value = mock_client
            await deliver_run_result_if_needed(detail)
            mock_client.chat_postMessage.assert_called_once()
            call_kwargs = mock_client.chat_postMessage.call_args.kwargs
            assert call_kwargs["channel"] == "C012AB3CD"
            assert call_kwargs["thread_ts"] == "1234567890.123456"
            assert detail.id in call_kwargs["text"]


@pytest.mark.asyncio
async def test_slack_delivery_approval_message_contains_draft():
    async with AsyncSessionLocal() as session:
        run = await create_run(
            session,
            template_key="yuno-chargeback-management",
            input_message=(
                "Chargeback received for TXN-9034 from iFood Brazil. "
                "Fraudulent transaction with duplicate auth."
            ),
            channel="slack",
            source_metadata={
                "channel": "C012AB3CD",
                "thread_ts": "1234567890.123456",
            },
        )
        run_id = run.id
        await execute_workflow_run(session, run_id)

    async with AsyncSessionLocal() as session:
        detail = await get_run(session, run_id)
        assert detail.status == "awaiting_approval"

    with patch("app.channels.slack_delivery.get_settings") as mock_settings:
        mock_settings.return_value.slack_bot_token = "xoxb-test-token"
        with patch(
            "app.channels.slack_delivery.AsyncWebClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_client_class.return_value = mock_client
            await deliver_run_result_if_needed(detail)
            mock_client.chat_postMessage.assert_called_once()
            call_kwargs = mock_client.chat_postMessage.call_args.kwargs
            assert "approval" in call_kwargs["text"].lower()