from datetime import datetime, timezone
from uuid import UUID

from codemind_ai_orchestrator import AIProvider, ClaudeAIProvider
from codemind_github_client import GitHubWriteClient
from codemind_shared_types.models import File, Finding, ProposedChange, User
from codemind_shared_types.schemas import FindingDetailDTO
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.deps import get_current_user, get_org_membership
from codemind_api.providers import get_real_ai_provider, get_github_write_client

router = APIRouter(prefix="/api/organizations/{org_id}/repositories/{repo_id}", tags=["proposed-changes"])


class ProposedChangeResponse(BaseModel):
    id: UUID
    finding_id: UUID
    file_id: UUID
    explanation: str
    updated_content: str
    test_file_path: str | None
    test_file_content: str | None
    generated_by: str
    status: str
    pr_url: str | None
    pr_number: int | None
    published_at: datetime | None


class PublishResponse(BaseModel):
    pr_url: str
    pr_number: int


def _to_response(proposed_change: ProposedChange) -> ProposedChangeResponse:
    return ProposedChangeResponse(
        id=proposed_change.id,
        finding_id=proposed_change.finding_id,
        file_id=proposed_change.file_id,
        explanation=proposed_change.explanation,
        updated_content=proposed_change.updated_content,
        test_file_path=proposed_change.test_file_path,
        test_file_content=proposed_change.test_file_content,
        generated_by=proposed_change.generated_by,
        status=proposed_change.status,
        pr_url=proposed_change.pr_url,
        pr_number=proposed_change.pr_number,
        published_at=proposed_change.published_at,
    )


async def _get_org_scoped_finding(db: AsyncSession, org_id: UUID, finding_id: UUID) -> Finding:
    finding = await db.get(Finding, finding_id)
    if finding is None or finding.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


async def _get_org_scoped_proposed_change(
    db: AsyncSession, org_id: UUID, proposed_change_id: UUID
) -> ProposedChange:
    proposed_change = await db.get(ProposedChange, proposed_change_id)
    if proposed_change is None or proposed_change.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposed change not found")
    return proposed_change


@router.post(
    "/findings/{finding_id}/propose-fix",
    response_model=ProposedChangeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def propose_fix(
    org_id: UUID,
    repo_id: UUID,
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_real_ai_provider),
    _membership=Depends(get_org_membership),
) -> ProposedChangeResponse:
    finding = await _get_org_scoped_finding(db, org_id, finding_id)
    file_row = await db.get(File, finding.file_id)
    if file_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    finding_dto = FindingDetailDTO(
        check_id=finding.check_id,
        category=finding.category,
        title=finding.title,
        severity=finding.severity,
        confidence=finding.confidence,
        explanation=finding.explanation,
        recommended_fix=finding.recommended_fix,
        suggested_test=finding.suggested_test,
        execution_path=finding.execution_path,
        file_path=file_row.path,
        start_line=finding.start_line,
        end_line=finding.end_line,
        evidence=finding.evidence,
    )
    fix = await ai_provider.propose_fix(finding=finding_dto, file_content=file_row.content)

    proposed_change = ProposedChange(
        organization_id=org_id,
        finding_id=finding.id,
        file_id=file_row.id,
        explanation=fix.explanation,
        updated_content=fix.updated_file_content,
        test_file_path=fix.test_file_path,
        test_file_content=fix.test_file_content,
        generated_by="claude" if isinstance(ai_provider, ClaudeAIProvider) else "mock",
    )
    db.add(proposed_change)
    await db.commit()
    await db.refresh(proposed_change)

    return _to_response(proposed_change)


@router.get("/proposed-changes/{proposed_change_id}", response_model=ProposedChangeResponse)
async def get_proposed_change(
    org_id: UUID,
    repo_id: UUID,
    proposed_change_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> ProposedChangeResponse:
    proposed_change = await _get_org_scoped_proposed_change(db, org_id, proposed_change_id)
    return _to_response(proposed_change)


@router.post("/proposed-changes/{proposed_change_id}/publish", response_model=PublishResponse)
async def publish_proposed_change(
    org_id: UUID,
    repo_id: UUID,
    proposed_change_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    write_client: GitHubWriteClient = Depends(get_github_write_client),
    _membership=Depends(get_org_membership),
) -> PublishResponse:
    proposed_change = await _get_org_scoped_proposed_change(db, org_id, proposed_change_id)
    if proposed_change.status == "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Proposed change already published"
        )

    if not settings.github_target_owner or not settings.github_target_repo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No publish target configured (GITHUB_TARGET_OWNER/GITHUB_TARGET_REPO)",
        )

    file_row = await db.get(File, proposed_change.file_id)
    if file_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    finding = await db.get(Finding, proposed_change.finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    owner = settings.github_target_owner
    repo = settings.github_target_repo
    base_branch = settings.github_target_base_branch
    remote_path = f"{settings.github_target_path_prefix}{file_row.path}"

    remote_file = await write_client.get_file(
        owner=owner, repo=repo, path=remote_path, branch=base_branch
    )
    if remote_file.content != file_row.content:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{remote_path} on {owner}/{repo}@{base_branch} has changed since this fix "
                "was generated — refresh and propose again before publishing."
            ),
        )

    new_branch = f"codemind/fix-{proposed_change.id}"
    await write_client.create_branch(
        owner=owner, repo=repo, base_branch=base_branch, new_branch=new_branch
    )
    await write_client.update_file(
        owner=owner,
        repo=repo,
        path=remote_path,
        branch=new_branch,
        content=proposed_change.updated_content,
        sha=remote_file.sha,
        message=f"CodeMind: {finding.title}",
    )
    if proposed_change.test_file_path and proposed_change.test_file_content:
        await write_client.update_file(
            owner=owner,
            repo=repo,
            path=f"{settings.github_target_path_prefix}{proposed_change.test_file_path}",
            branch=new_branch,
            content=proposed_change.test_file_content,
            sha=None,
            message=f"CodeMind: add test for {finding.title}",
        )

    pull_request = await write_client.create_pull_request(
        owner=owner,
        repo=repo,
        head_branch=new_branch,
        base_branch=base_branch,
        title=f"CodeMind: {finding.title}",
        body=proposed_change.explanation,
        draft=True,
    )

    proposed_change.status = "published"
    proposed_change.pr_url = pull_request.url
    proposed_change.pr_number = pull_request.number
    proposed_change.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    proposed_change.published_by = user.id
    await db.commit()

    return PublishResponse(pr_url=pull_request.url, pr_number=pull_request.number)
