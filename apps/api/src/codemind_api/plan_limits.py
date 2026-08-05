from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_shared_types.models import FindingExplanation, PRReview, ProposedChange, Repository

PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "free": {"repositories": 1, "ai_actions_per_month": 20},
    "pro": {"repositories": 10, "ai_actions_per_month": 500},
    "team": {"repositories": None, "ai_actions_per_month": None},
}


def _month_start() -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def count_repositories(db: AsyncSession, org_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Repository).where(Repository.organization_id == org_id)
    )
    return result.scalar_one()


async def count_ai_actions_this_month(db: AsyncSession, org_id: UUID) -> int:
    month_start = _month_start()
    total = 0
    for model in (ProposedChange, FindingExplanation, PRReview):
        result = await db.execute(
            select(func.count())
            .select_from(model)
            .where(model.organization_id == org_id, model.created_at >= month_start)
        )
        total += result.scalar_one()
    return total


RESOURCE_COUNTERS: dict[str, Callable[[AsyncSession, UUID], Coroutine[Any, Any, int]]] = {
    "repositories": count_repositories,
    "ai_actions_per_month": count_ai_actions_this_month,
}
