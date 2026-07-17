from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.repository_index_utils import get_latest_completed_index
from codemind_shared_types.models import RepositorySummary

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["summary"])


class DirectorySummary(BaseModel):
    path: str
    summary: str


class SummaryResponse(BaseModel):
    repository_summary: str | None
    directories: list[DirectorySummary]


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> SummaryResponse:
    repository_index = await get_latest_completed_index(db, repo_id)
    if repository_index is None:
        return SummaryResponse(repository_summary=None, directories=[])

    result = await db.execute(
        select(RepositorySummary).where(
            RepositorySummary.repository_index_id == repository_index.id
        )
    )
    summaries = result.scalars().all()
    repo_summary = next((s.summary for s in summaries if s.scope == "repository"), None)
    directories = sorted(
        (DirectorySummary(path=s.path, summary=s.summary) for s in summaries if s.scope == "directory"),
        key=lambda d: d.path,
    )
    return SummaryResponse(repository_summary=repo_summary, directories=directories)
