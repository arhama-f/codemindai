from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_shared_types.models import AnalysisRun, RepositoryIndex


async def get_latest_completed_index(
    db: AsyncSession, repository_id: UUID
) -> RepositoryIndex | None:
    result = await db.execute(
        select(RepositoryIndex)
        .where(
            RepositoryIndex.repository_id == repository_id,
            RepositoryIndex.status == "completed",
        )
        .order_by(RepositoryIndex.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_analysis_run(db: AsyncSession, repository_id: UUID) -> AnalysisRun | None:
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.repository_id == repository_id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_completed_analysis_run(
    db: AsyncSession, repository_id: UUID
) -> AnalysisRun | None:
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.repository_id == repository_id, AnalysisRun.status == "completed")
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
