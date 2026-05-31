from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.runs import MetricsRead
from app.services.run_service import metrics

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics", response_model=MetricsRead)
async def get_metrics_route(
    session: AsyncSession = Depends(get_session),
):
    return await metrics(session)