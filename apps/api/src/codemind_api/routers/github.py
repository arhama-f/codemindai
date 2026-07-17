from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.providers import get_github_client
from codemind_github_client import GitHubClient
from codemind_shared_types.models import GithubInstallation, OrganizationMember

router = APIRouter(prefix="/api/organizations/{org_id}/github", tags=["github"])


class InstallationResponse(BaseModel):
    installation_id: UUID
    account_login: str


class RepositoryListingResponse(BaseModel):
    external_repo_id: str
    full_name: str
    default_branch: str


@router.post("/connect", response_model=InstallationResponse)
async def connect_github(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    github_client: GitHubClient = Depends(get_github_client),
    membership: OrganizationMember = Depends(get_org_membership),
) -> InstallationResponse:
    existing = await db.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation = existing.scalar_one_or_none()
    if installation is None:
        [remote_installation] = await github_client.list_installations(user_id=str(membership.user_id))
        installation = GithubInstallation(
            organization_id=org_id,
            provider="mock",
            external_installation_id=remote_installation.external_installation_id,
            account_login=remote_installation.account_login,
        )
        db.add(installation)
        await db.commit()
        await db.refresh(installation)

    return InstallationResponse(installation_id=installation.id, account_login=installation.account_login)


@router.get("/repositories", response_model=list[RepositoryListingResponse])
async def list_available_repositories(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    github_client: GitHubClient = Depends(get_github_client),
    _membership: OrganizationMember = Depends(get_org_membership),
) -> list[RepositoryListingResponse]:
    result = await db.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation = result.scalar_one_or_none()
    if installation is None:
        return []

    repos = await github_client.list_repositories(
        installation_id=installation.external_installation_id
    )
    return [
        RepositoryListingResponse(
            external_repo_id=r.external_repo_id,
            full_name=r.full_name,
            default_branch=r.default_branch,
        )
        for r in repos
    ]
