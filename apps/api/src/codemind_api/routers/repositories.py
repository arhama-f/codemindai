from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.providers import get_github_client
from codemind_api.repository_index_utils import get_latest_analysis_run
from codemind_github_client import GitHubClient
from codemind_shared_types.models import GithubInstallation, Repository, RepositoryIndex

router = APIRouter(prefix="/api/organizations/{org_id}/repositories", tags=["repositories"])


class AddRepositoryRequest(BaseModel):
    external_repo_id: str


class RepositoryResponse(BaseModel):
    id: UUID
    full_name: str
    default_branch: str
    latest_index_status: str | None = None
    latest_index_id: UUID | None = None
    latest_analysis_status: str | None = None
    latest_analysis_id: UUID | None = None


async def _latest_index(db: AsyncSession, repository_id: UUID) -> RepositoryIndex | None:
    result = await db.execute(
        select(RepositoryIndex)
        .where(RepositoryIndex.repository_id == repository_id)
        .order_by(RepositoryIndex.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _to_response(db: AsyncSession, repository: Repository) -> RepositoryResponse:
    latest_index = await _latest_index(db, repository.id)
    latest_analysis = await get_latest_analysis_run(db, repository.id)
    return RepositoryResponse(
        id=repository.id,
        full_name=repository.full_name,
        default_branch=repository.default_branch,
        latest_index_status=latest_index.status if latest_index else None,
        latest_index_id=latest_index.id if latest_index else None,
        latest_analysis_status=latest_analysis.status if latest_analysis else None,
        latest_analysis_id=latest_analysis.id if latest_analysis else None,
    )


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def add_repository(
    org_id: UUID,
    payload: AddRepositoryRequest,
    db: AsyncSession = Depends(get_db),
    github_client: GitHubClient = Depends(get_github_client),
    _membership=Depends(get_org_membership),
) -> RepositoryResponse:
    installation_result = await db.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation = installation_result.scalar_one_or_none()
    if installation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="GitHub is not connected for this organization"
        )

    existing = await db.execute(
        select(Repository).where(
            Repository.organization_id == org_id,
            Repository.external_repo_id == payload.external_repo_id,
        )
    )
    repository = existing.scalar_one_or_none()
    if repository is not None:
        return await _to_response(db, repository)

    available = await github_client.list_repositories(
        installation_id=installation.external_installation_id
    )
    remote_repo = next(
        (r for r in available if r.external_repo_id == payload.external_repo_id), None
    )
    if remote_repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    repository = Repository(
        organization_id=org_id,
        installation_id=installation.id,
        external_repo_id=remote_repo.external_repo_id,
        full_name=remote_repo.full_name,
        default_branch=remote_repo.default_branch,
    )
    db.add(repository)
    await db.commit()
    await db.refresh(repository)

    return await _to_response(db, repository)


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> list[RepositoryResponse]:
    result = await db.execute(select(Repository).where(Repository.organization_id == org_id))
    repositories = result.scalars().all()
    return [await _to_response(db, repo) for repo in repositories]


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    org_id: UUID,
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> RepositoryResponse:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.organization_id == org_id)
    )
    repository = result.scalar_one_or_none()
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return await _to_response(db, repository)
