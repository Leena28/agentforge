import os
import pytest
import pytest_asyncio

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_agentforge.db"
os.environ["RUN_WORKFLOWS_INLINE"] = "true"
os.environ["ENABLE_LLM"] = "false"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["PGVECTOR_ENABLED"] = "false"

from app.db.session import engine, init_db
from app.db.base import Base
from app.seed import seed


@pytest_asyncio.fixture(autouse=True)
async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)