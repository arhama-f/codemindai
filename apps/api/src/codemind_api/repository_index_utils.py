from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_shared_types.models import RepositoryIndex


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
