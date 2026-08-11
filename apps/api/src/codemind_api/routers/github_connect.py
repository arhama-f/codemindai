import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.deps import get_current_user, get_org_membership
from codemind_api.providers import get_github_repo_oauth_provider
from codemind_oauth_client import GitHubOAuthProvider
from codemind_shared_types.models import GithubInstallation, OrganizationMember, User

router = APIRouter(prefix="/api/organizations", tags=["github"])

GITHUB_CONNECT_STATE_COOKIE = "github_connect_state"


@router.get("/{org_id}/github/connect/start")
async def github_connect_start(
    org_id: UUID,
    oauth_provider: GitHubOAuthProvider = Depends(get_github_repo_oauth_provider),
    _membership: OrganizationMember = Depends(get_org_membership),
) -> RedirectResponse:
    state = f"{org_id}:{secrets.token_urlsafe(16)}"

    response = RedirectResponse(
        url=oauth_provider.authorize_url(state=state, scope="repo"), status_code=status.HTTP_302_FOUND
    )
    response.set_cookie(
        key=GITHUB_CONNECT_STATE_COOKIE, value=state, httponly=True, samesite="lax", max_age=600
    )
    return response


@router.get("/github/connect/callback")
async def github_connect_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    oauth_provider: GitHubOAuthProvider = Depends(get_github_repo_oauth_provider),
) -> RedirectResponse:
    cookie_state = request.cookies.get(GITHUB_CONNECT_STATE_COOKIE)
    if cookie_state is None or cookie_state != state:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    org_id_str, _, _nonce = state.partition(":")
    try:
        org_id = UUID(org_id_str)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from None

    membership_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if membership_result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

    oauth_user = await oauth_provider.exchange_code(code=code)

    installation_result = await db.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation = installation_result.scalar_one_or_none()
    account_login = oauth_user.username or oauth_user.full_name or oauth_user.email

    if installation is None:
        installation = GithubInstallation(
            organization_id=org_id,
            provider="github",
            external_installation_id=oauth_user.provider_user_id,
            account_login=account_login,
            access_token=oauth_user.access_token,
        )
        db.add(installation)
    else:
        installation.provider = "github"
        installation.external_installation_id = oauth_user.provider_user_id
        installation.account_login = account_login
        installation.access_token = oauth_user.access_token

    await db.commit()

    response = RedirectResponse(
        url=f"{settings.web_origin}/orgs/{org_id}", status_code=status.HTTP_302_FOUND
    )
    response.delete_cookie(GITHUB_CONNECT_STATE_COOKIE)
    return response
