import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import SessionLocal, get_db
from codemind_api.deps import get_org_membership
from codemind_shared_types.models import JobRun, Repository

router = APIRouter(prefix="/api/organizations/{org_id}", tags=["indexing"])

_POLL_INTERVAL_SECONDS = 0.5
_TERMINAL_STATUSES = {"completed", "failed"}


class StartIndexResponse(BaseModel):
    job_id: UUID


class JobResponse(BaseModel):
    status: str
    progress_percent: int
    message: str | None = None
    error_message: str | None = None


def get_redis_pool(request: Request):
    return request.app.state.redis_pool


@router.post(
    "/repositories/{repo_id}/index",
    response_model=StartIndexResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_indexing(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_pool=Depends(get_redis_pool),
    _membership=Depends(get_org_membership),
) -> StartIndexResponse:
    repository = await db.get(Repository, repo_id)
    if repository is None or repository.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    job_run = JobRun(organization_id=org_id, repository_id=repo_id, job_type="index_repository")
    db.add(job_run)
    await db.commit()
    await db.refresh(job_run)

    arq_job = await redis_pool.enqueue_job(
        "index_repository", repository_id=str(repo_id), job_run_id=str(job_run.id)
    )
    job_run.arq_job_id = arq_job.job_id if arq_job is not None else None
    await db.commit()

    return StartIndexResponse(job_id=job_run.id)


async def _get_org_scoped_job(db: AsyncSession, org_id: UUID, job_id: UUID) -> JobRun:
    job_run = await db.get(JobRun, job_id)
    if job_run is None or job_run.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job_run


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    org_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> JobRun:
    return await _get_org_scoped_job(db, org_id, job_id)


@router.get("/jobs/{job_id}/events")
async def stream_job_events(
    org_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> StreamingResponse:
    # Validate access/existence up front using the request-scoped session;
    # the generator below opens its own short-lived sessions per poll so it
    # isn't tied to a session that outlives this request's dependency scope.
    await _get_org_scoped_job(db, org_id, job_id)

    async def event_generator():
        while True:
            async with SessionLocal() as session:
                job_run = await session.get(JobRun, job_id)
                if job_run is None:
                    return
                payload = json.dumps(
                    {
                        "status": job_run.status,
                        "progress_percent": job_run.progress_percent,
                        "message": job_run.message,
                    }
                )
                yield f"data: {payload}\n\n"
                if job_run.status in _TERMINAL_STATUSES:
                    return
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
