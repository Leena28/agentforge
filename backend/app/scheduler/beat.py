import asyncio
from datetime import UTC, datetime

from celery import Celery
from celery.schedules import crontab

from app.config.settings import get_settings
from app.core.logging import logger

settings = get_settings()


def build_beat_schedule(agents: list[dict]) -> dict:
    schedule = {}
    for agent in agents:
        agent_id = agent.get("id")
        agent_name = agent.get("name", "unknown")
        schedules = agent.get("schedules", {})
        template_key = agent.get("runtime_node_binding")

        if not schedules or schedules.get("mode") == "on_demand":
            continue

        if not template_key:
            continue

        mode = schedules.get("mode")
        cron = schedules.get("cron")
        input_message = schedules.get(
            "input_message",
            f"Scheduled run triggered for agent {agent_name}",
        )

        if mode == "daily":
            hour = schedules.get("hour", 9)
            minute = schedules.get("minute", 0)
            schedule[f"scheduled_{agent_id}"] = {
                "task": "workflow.execute_scheduled",
                "schedule": crontab(hour=hour, minute=minute),
                "args": [template_key, input_message, agent_id],
            }
        elif mode == "hourly":
            minute = schedules.get("minute", 0)
            schedule[f"scheduled_{agent_id}"] = {
                "task": "workflow.execute_scheduled",
                "schedule": crontab(minute=minute),
                "args": [template_key, input_message, agent_id],
            }
        elif mode == "cron" and cron:
            parts = cron.strip().split()
            if len(parts) == 5:
                minute, hour, day_of_month, month_of_year, day_of_week = parts
                schedule[f"scheduled_{agent_id}"] = {
                    "task": "workflow.execute_scheduled",
                    "schedule": crontab(
                        minute=minute,
                        hour=hour,
                        day_of_month=day_of_month,
                        month_of_year=month_of_year,
                        day_of_week=day_of_week,
                    ),
                    "args": [template_key, input_message, agent_id],
                }

        if f"scheduled_{agent_id}" in schedule:
            logger.info(
                "beat_schedule_added",
                agent_id=agent_id,
                agent_name=agent_name,
                mode=mode,
            )

    return schedule


async def load_schedule_from_db() -> dict:
    from app.db.session import AsyncSessionLocal
    from app.db.models.agents import Agent
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Agent))
        agents = result.scalars().all()
        agent_dicts = [
            {
                "id": agent.id,
                "name": agent.name,
                "schedules": agent.schedules,
                "runtime_node_binding": agent.runtime_node_binding,
            }
            for agent in agents
        ]
    return build_beat_schedule(agent_dicts)


def setup_celery_beat(celery_app: Celery) -> None:
    async def _load() -> None:
        schedule = await load_schedule_from_db()
        celery_app.conf.beat_schedule = schedule
        celery_app.conf.timezone = "UTC"
        logger.info(
            "beat_schedule_loaded",
            total_scheduled_tasks=len(schedule),
        )

    asyncio.run(_load())
    logger.info("celery_beat_configured")