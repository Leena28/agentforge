from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.monitoring import router as monitoring_router
from app.api.runs import router as runs_router
from app.api.templates import router as templates_router
from app.config.settings import get_settings
from app.core.logging import configure_logging, logger
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info("startup", app=settings.app_name, env=settings.app_env)
    await init_db()
    if settings.seed_demo_data:
        from app.seed import seed
        await seed()
    yield
    logger.info("shutdown", app=settings.app_name)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI Agent Orchestration Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
    }