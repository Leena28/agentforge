import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session, AsyncSessionLocal
from app.schemas.runs import (
    ApproveRunRequest,
    StartRunRequest,
    StartRunResponse,
    WorkflowRunDetail,
    WorkflowRunRead,
)
from app.services.run_service import (
    approve_run,
    create_and_dispatch_run,
    get_run,
    list_runs,
    stream_run_events,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[WorkflowRunRead])
async def list_runs_route(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    return await list_runs(session, limit=limit)


@router.post("", response_model=StartRunResponse)
async def start_run_route(
    payload: StartRunRequest,
    session: AsyncSession = Depends(get_session),
):
    return await create_and_dispatch_run(session, payload)


@router.get("/{run_id}", response_model=WorkflowRunDetail)
async def get_run_route(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/approve", response_model=WorkflowRunDetail)
async def approve_run_route(
    run_id: str,
    payload: ApproveRunRequest,
    session: AsyncSession = Depends(get_session),
):
    run = await get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail="Run is not awaiting approval"
        )
    return await approve_run(session, run, payload)


@router.get("/{run_id}/events/stream")
async def stream_run_events_route(run_id: str):
    return StreamingResponse(
        stream_run_events(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )