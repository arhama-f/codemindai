from datetime import datetime
from uuid import UUID

from codemind_analysis_engine import analyze_file, filter_findings_to_added_lines
from codemind_code_parser import parse_file
from codemind_github_client import GitHubWriteClient, parse_patch_added_lines
from codemind_shared_types.models import PRReview, User
from codemind_shared_types.schemas import FindingDraftDTO, ReviewCommentDTO
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.deps import get_current_user, get_org_membership
from codemind_api.providers import get_ai_provider_for_fix, get_github_write_client

router = APIRouter(prefix="/api/organizations/{org_id}/pr-reviews", tags=["pr-review"])

_ANALYZABLE_EXTENSIONS = (".ts", ".tsx")
_BLOCKING_SEVERITIES = {"critical", "high"}
_STATUS_CONTEXT = "codemind-ai/pr-review"


class StartPRReviewRequest(BaseModel):
    pr_number: int


class PRReviewResponse(BaseModel):
    id: UUID
    owner: str
    repo: str
    pr_number: int
    pr_url: str
    commit_sha: str
    findings_count: int
    comments_posted: int
    status: str
    review_url: str | None
    created_at: datetime


def _to_response(pr_review: PRReview) -> PRReviewResponse:
    return PRReviewResponse(
        id=pr_review.id,
        owner=pr_review.owner,
        repo=pr_review.repo,
        pr_number=pr_review.pr_number,
        pr_url=f"https://github.com/{pr_review.owner}/{pr_review.repo}/pull/{pr_review.pr_number}",
        commit_sha=pr_review.commit_sha,
        findings_count=pr_review.findings_count,
        comments_posted=pr_review.comments_posted,
        status=pr_review.status,
        review_url=pr_review.review_url,
        created_at=pr_review.created_at,
    )


def _format_comment(finding: FindingDraftDTO) -> str:
    return (
        f"**{finding.severity.upper()} · {finding.category}: {finding.title}**\n\n"
        f"{finding.explanation}\n\n"
        f"**Recommended fix:** {finding.recommended_fix}"
    )


async def _get_org_scoped_pr_review(
    db: AsyncSession, org_id: UUID, pr_review_id: UUID
) -> PRReview:
    pr_review = await db.get(PRReview, pr_review_id)
    if pr_review is None or pr_review.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR review not found")
    return pr_review


@router.post("", response_model=PRReviewResponse, status_code=status.HTTP_201_CREATED)
async def review_pull_request(
    org_id: UUID,
    payload: StartPRReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    write_client: GitHubWriteClient = Depends(get_github_write_client),
    ai_provider=Depends(get_ai_provider_for_fix),
    _membership=Depends(get_org_membership),
) -> PRReviewResponse:
    if not settings.github_target_owner or not settings.github_target_repo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No target repo configured (GITHUB_TARGET_OWNER/GITHUB_TARGET_REPO)",
        )

    owner = settings.github_target_owner
    repo = settings.github_target_repo

    pr = await write_client.get_pull_request(owner=owner, repo=repo, pr_number=payload.pr_number)
    files = await write_client.get_pull_request_files(
        owner=owner, repo=repo, pr_number=payload.pr_number
    )

    relevant_findings: list[FindingDraftDTO] = []
    comments: list[ReviewCommentDTO] = []

    for pr_file in files:
        if pr_file.status == "removed" or not pr_file.path.endswith(_ANALYZABLE_EXTENSIONS):
            continue
        if not pr_file.patch:
            continue

        added_lines = parse_patch_added_lines(pr_file.patch)
        if not added_lines:
            continue

        remote_file = await write_client.get_file(
            owner=owner, repo=repo, path=pr_file.path, branch=pr.head_ref
        )
        parsed = parse_file(pr_file.path, remote_file.content)
        findings = analyze_file(pr_file.path, remote_file.content, parsed.symbols)
        for finding in filter_findings_to_added_lines(findings, added_lines):
            relevant_findings.append(finding)
            comments.append(
                ReviewCommentDTO(
                    path=pr_file.path, line=finding.start_line, body=_format_comment(finding)
                )
            )

    review_url: str | None = None
    if comments:
        summary = await ai_provider.summarize_pr_review(
            pr_title=pr.title, findings=relevant_findings
        )
        review = await write_client.create_review(
            owner=owner,
            repo=repo,
            pr_number=pr.number,
            commit_sha=pr.head_sha,
            body=summary,
            comments=comments,
        )
        review_url = review.html_url

    review_status = (
        "failure"
        if any(f.severity in _BLOCKING_SEVERITIES for f in relevant_findings)
        else "success"
    )
    status_description = (
        f"{len(relevant_findings)} issue(s) found in this PR's diff"
        if relevant_findings
        else "No issues found in this PR's diff"
    )
    await write_client.create_commit_status(
        owner=owner,
        repo=repo,
        sha=pr.head_sha,
        state=review_status,
        description=status_description,
        context=_STATUS_CONTEXT,
    )

    pr_review = PRReview(
        organization_id=org_id,
        owner=owner,
        repo=repo,
        pr_number=pr.number,
        commit_sha=pr.head_sha,
        findings_count=len(relevant_findings),
        comments_posted=len(comments),
        status=review_status,
        review_url=review_url,
        reviewed_by=user.id,
    )
    db.add(pr_review)
    await db.commit()
    await db.refresh(pr_review)

    return _to_response(pr_review)


@router.get("/{pr_review_id}", response_model=PRReviewResponse)
async def get_pr_review(
    org_id: UUID,
    pr_review_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> PRReviewResponse:
    pr_review = await _get_org_scoped_pr_review(db, org_id, pr_review_id)
    return _to_response(pr_review)
