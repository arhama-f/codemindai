from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.auth_tokens import create_password_reset_token, hash_token, is_expired
from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.providers import get_email_provider
from codemind_api.security import hash_password
from codemind_email_provider import EmailProvider
from codemind_shared_types.models import PasswordReset, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    payload: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> None:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # Always return 204 whether or not the email exists — avoids leaking
    # account existence to an unauthenticated caller.
    if user is None:
        return

    reset = await create_password_reset_token(db, user_id=user.id)
    await db.commit()

    reset_link = f"{settings.web_origin}/reset-password/{reset.raw_token}"
    await email_provider.send(
        to=user.email,
        subject="Reset your CodeMind AI password",
        html_body=f'<p>Reset your password: <a href="{reset_link}">{reset_link}</a>.</p>',
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> None:
    result = await db.execute(
        select(PasswordReset).where(PasswordReset.token_hash == hash_token(payload.token))
    )
    reset = result.scalar_one_or_none()
    if reset is None or reset.used_at is not None or is_expired(reset.expires_at):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user = await db.get(User, reset.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user.password_hash = hash_password(payload.new_password)
    reset.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
