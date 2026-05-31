from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.logging import logger

settings = get_settings()


async def ensure_vector_extension(session: AsyncSession) -> None:
    try:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await session.commit()
        logger.info("pgvector_extension_ready")
    except Exception as exc:
        logger.warning("pgvector_extension_failed", error=str(exc))


async def ensure_memory_table(session: AsyncSession) -> None:
    try:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(36) NOT NULL,
                run_id VARCHAR(36),
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS agent_memory_embedding_idx
            ON agent_memory
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS agent_memory_agent_id_idx
            ON agent_memory (agent_id)
        """))
        await session.commit()
        logger.info("agent_memory_table_ready")
    except Exception as exc:
        logger.warning("agent_memory_table_failed", error=str(exc))


async def store_memory(
    session: AsyncSession,
    agent_id: str,
    content: str,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    if not settings.pgvector_enabled:
        return None
    try:
        embedding = await _get_embedding(content)
        if not embedding:
            return None
        result = await session.execute(
            text("""
                INSERT INTO agent_memory
                    (agent_id, run_id, content, embedding, metadata)
                VALUES
                    (:agent_id, :run_id, :content, :embedding, :metadata)
                RETURNING id
            """),
            {
                "agent_id": agent_id,
                "run_id": run_id,
                "content": content,
                "embedding": str(embedding),
                "metadata": metadata or {},
            },
        )
        await session.commit()
        memory_id = str(result.scalar())
        logger.info(
            "memory_stored",
            agent_id=agent_id,
            run_id=run_id,
            memory_id=memory_id,
        )
        return memory_id
    except Exception as exc:
        logger.warning("memory_store_failed", error=str(exc), agent_id=agent_id)
        return None


async def retrieve_memory(
    session: AsyncSession,
    agent_id: str,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not settings.pgvector_enabled:
        return []
    try:
        query_embedding = await _get_embedding(query)
        if not query_embedding:
            return []
        result = await session.execute(
            text("""
                SELECT
                    id,
                    content,
                    metadata,
                    created_at,
                    1 - (embedding <=> :query_embedding) AS similarity
                FROM agent_memory
                WHERE agent_id = :agent_id
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """),
            {
                "agent_id": agent_id,
                "query_embedding": str(query_embedding),
                "limit": limit,
            },
        )
        rows = result.fetchall()
        memories = [
            {
                "id": str(row.id),
                "content": row.content,
                "metadata": row.metadata,
                "created_at": row.created_at.isoformat(),
                "similarity": round(float(row.similarity), 4),
            }
            for row in rows
        ]
        logger.info(
            "memory_retrieved",
            agent_id=agent_id,
            results=len(memories),
        )
        return memories
    except Exception as exc:
        logger.warning(
            "memory_retrieve_failed",
            error=str(exc),
            agent_id=agent_id,
        )
        return []


async def _get_embedding(text_input: str) -> list[float] | None:
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text_input,
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("embedding_failed", error=str(exc))
        return None


async def list_memories(
    session: AsyncSession,
    agent_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    try:
        result = await session.execute(
            text("""
                SELECT id, content, metadata, created_at
                FROM agent_memory
                WHERE agent_id = :agent_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"agent_id": agent_id, "limit": limit},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "metadata": row.metadata,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    except Exception as exc:
        logger.warning(
            "memory_list_failed",
            error=str(exc),
            agent_id=agent_id,
        )
        return []


async def delete_memory(
    session: AsyncSession,
    agent_id: str,
    memory_id: str,
) -> bool:
    try:
        await session.execute(
            text("""
                DELETE FROM agent_memory
                WHERE id = :memory_id AND agent_id = :agent_id
            """),
            {"memory_id": memory_id, "agent_id": agent_id},
        )
        await session.commit()
        logger.info(
            "memory_deleted",
            agent_id=agent_id,
            memory_id=memory_id,
        )
        return True
    except Exception as exc:
        logger.warning(
            "memory_delete_failed",
            error=str(exc),
            agent_id=agent_id,
        )
        return False