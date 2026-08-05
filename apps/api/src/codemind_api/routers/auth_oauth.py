import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.providers import get_oauth_provider
from codemind_api.security import set_session_cookie
from codemind_oauth_client import OAuthProvider
from codemind_shared_types.models import User, UserOAuthIdentity

router = APIRouter(prefix="/api/auth/oauth", tags=["auth"])

OAUTH_STATE_COOKIE = "oauth_state"


@router.get("/{provider}/start")
async def oauth_start(
    provider: str, oauth_provider: OAuthProvider = Depends(get_oauth_provider)
) -> RedirectResponse:
    state = secrets.token_urlsafe(16)

    response = RedirectResponse(url=oauth_provider.authorize_url(state=state), status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE, value=state, httponly=True, samesite="lax", max_age=600
    )
    return response


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    oauth_provider: OAuthProvider = Depends(get_oauth_provider),
) -> RedirectResponse:
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if cookie_state is None or cookie_state != state:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    oauth_user = await oauth_provider.exchange_code(code=code)

    identity_result = await db.execute(
        select(UserOAuthIdentity).where(
            UserOAuthIdentity.provider == provider,
            UserOAuthIdentity.provider_user_id == oauth_user.provider_user_id,
        )
    )
    identity = identity_result.scalar_one_or_none()

    if identity is not None:
        user = await db.get(User, identity.user_id)
    else:
        existing_result = await db.execute(select(User).where(User.email == oauth_user.email))
        user = existing_result.scalar_one_or_none()
        if user is None:
            user = User(
                email=oauth_user.email,
                password_hash=None,
                full_name=oauth_user.full_name or oauth_user.email,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
        db.add(
            UserOAuthIdentity(
                user_id=user.id, provider=provider, provider_user_id=oauth_user.provider_user_id
            )
        )

    await db.commit()

    response = RedirectResponse(url=f"{settings.web_origin}/orgs", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    set_session_cookie(response, user.id)
    return response
