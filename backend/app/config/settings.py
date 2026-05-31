from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # app
    app_name: str = "AgentForge"
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"

    # database
    database_url: str = "postgresql+asyncpg://yuno:yuno@localhost:5432/yuno_agentops"

    # redis
    redis_url: str = "redis://localhost:6379/0"

    # llm
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 30
    enable_llm: bool = True
    openai_api_key: str | None = None

    # slack
    slack_bot_token: str | None = None
    slack_app_token: str | None = None
    slack_signing_secret: str | None = None
    slack_default_template: str = "payment-dispute-resolution"

    # celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # memory
    pgvector_enabled: bool = True
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # observability
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "http://localhost:3000"

    # feature flags
    run_workflows_inline: bool = False
    seed_demo_data: bool = True
    cors_origins: list[str] = Field(default_factory=list)

    @property
    def allowed_origins(self) -> list[str]:
        origins = [
            self.frontend_origin,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        return sorted(set(origins + self.cors_origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()