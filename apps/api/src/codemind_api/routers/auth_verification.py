from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.auth_tokens import create_verification_token, hash_token, is_expired
from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.deps import get_current_user
from codemind_api.providers import get_email_provider
from codemind_email_provider import EmailProvider
from codemind_shared_types.models import EmailVerification, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class VerifyEmailResponse(BaseModel):
    verified: bool


@router.get("/verify-email/{token}", response_model=VerifyEmailResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)) -> VerifyEmailResponse:
    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token_hash == hash_token(token))
    )
    verification = result.scalar_one_or_none()
    if verification is None or verification.used_at is not None or is_expired(verification.expires_at):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link")

    verification.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user = await db.get(User, verification.user_id)
    if user is not None:
        user.is_verified = True
    await db.commit()

    return VerifyEmailResponse(verified=True)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> None:
    if user.is_verified:
        return

    verification = await create_verification_token(db, user_id=user.id)
    await db.commit()

    verify_link = f"{settings.web_origin}/verify-email/{verification.raw_token}"
    await email_provider.send(
        to=user.email,
        subject="Verify your CodeMind AI email",
        html_body=f'<p>Welcome to CodeMind AI. <a href="{verify_link}">Verify your email</a>.</p>',
    )
