from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_current_user, get_org_membership
from codemind_api.repository_index_utils import get_latest_completed_analysis_run
from codemind_api.routers.indexing import get_redis_pool
from codemind_shared_types.models import File, Finding, JobRun, Repository, User

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["findings"])


class StartAnalysisResponse(BaseModel):
    job_id: UUID


class FindingSummary(BaseModel):
    id: UUID
    check_id: str
    category: str
    title: str
    severity: str
    confidence: str
    file_id: UUID
    file_path: str
    start_line: int
    end_line: int
    status: str


class FindingDetail(FindingSummary):
    explanation: str
    recommended_fix: str
    suggested_test: str | None
    execution_path: str | None
    evidence: list[dict]
    dismissed_reason: str | None
    dismissed_at: datetime | None


class DismissFindingRequest(BaseModel):
    reason: str


@router.post(
    "/analyses", response_model=StartAnalysisResponse, status_code=status.HTTP_202_ACCEPTED
)
async def start_analysis(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_pool=Depends(get_redis_pool),
    _membership=Depends(get_org_membership),
) -> StartAnalysisResponse:
    repository = await db.get(Repository, repo_id)
    if repository is None or repository.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    job_run = JobRun(organization_id=org_id, repository_id=repo_id, job_type="analyze_repository")
    db.add(job_run)
    await db.commit()
    await db.refresh(job_run)

    arq_job = await redis_pool.enqueue_job(
        "analyze_repository", repository_id=str(repo_id), job_run_id=str(job_run.id)
    )
    job_run.arq_job_id = arq_job.job_id if arq_job is not None else None
    await db.commit()

    return StartAnalysisResponse(job_id=job_run.id)


def _to_summary(finding: Finding, file_path: str) -> FindingSummary:
    return FindingSummary(
        id=finding.id,
        check_id=finding.check_id,
        category=finding.category,
        title=finding.title,
        severity=finding.severity,
        confidence=finding.confidence,
        file_id=finding.file_id,
        file_path=file_path,
        start_line=finding.start_line,
        end_line=finding.end_line,
        status=finding.status,
    )


@router.get("/findings", response_model=list[FindingSummary])
async def list_findings(
    org_id: UUID,
    repo_id: UUID,
    category: str | None = None,
    severity: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> list[FindingSummary]:
    analysis_run = await get_latest_completed_analysis_run(db, repo_id)
    if analysis_run is None:
        return []

    stmt = (
        select(Finding, File.path)
        .join(File, File.id == Finding.file_id)
        .where(Finding.analysis_run_id == analysis_run.id)
    )
    if category is not None:
        stmt = stmt.where(Finding.category == category)
    if severity is not None:
        stmt = stmt.where(Finding.severity == severity)
    if status_filter is not None:
        stmt = stmt.where(Finding.status == status_filter)
    stmt = stmt.order_by(Finding.severity, Finding.start_line)

    result = await db.execute(stmt)
    return [_to_summary(finding, file_path) for finding, file_path in result.all()]


async def _get_org_scoped_finding(db: AsyncSession, org_id: UUID, finding_id: UUID) -> Finding:
    finding = await db.get(Finding, finding_id)
    if finding is None or finding.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


async def _to_detail(db: AsyncSession, finding: Finding) -> FindingDetail:
    file_row = await db.get(File, finding.file_id)
    file_path = file_row.path if file_row is not None else ""
    return FindingDetail(
        **_to_summary(finding, file_path).model_dump(),
        explanation=finding.explanation,
        recommended_fix=finding.recommended_fix,
        suggested_test=finding.suggested_test,
        execution_path=finding.execution_path,
        evidence=finding.evidence,
        dismissed_reason=finding.dismissed_reason,
        dismissed_at=finding.dismissed_at,
    )


@router.get("/findings/{finding_id}", response_model=FindingDetail)
async def get_finding(
    org_id: UUID,
    repo_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> FindingDetail:
    finding = await _get_org_scoped_finding(db, org_id, finding_id)
    return await _to_detail(db, finding)


@router.post("/findings/{finding_id}/dismiss", response_model=FindingDetail)
async def dismiss_finding(
    org_id: UUID,
    repo_id: UUID,
    finding_id: UUID,
    payload: DismissFindingRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _membership=Depends(get_org_membership),
) -> FindingDetail:
    finding = await _get_org_scoped_finding(db, org_id, finding_id)

    finding.status = "dismissed"
    finding.dismissed_reason = payload.reason
    finding.dismissed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    finding.dismissed_by = user.id
    await db.commit()
    await db.refresh(finding)

    return await _to_detail(db, finding)
