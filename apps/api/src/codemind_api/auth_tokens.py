import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from codemind_shared_types.models import EmailVerification, PasswordReset

VERIFICATION_TOKEN_TTL = timedelta(hours=24)
PASSWORD_RESET_TOKEN_TTL = timedelta(hours=1)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class IssuedToken:
    raw_token: str
    expires_at: datetime


async def create_verification_token(db: AsyncSession, *, user_id: UUID) -> IssuedToken:
    raw_token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + VERIFICATION_TOKEN_TTL
    db.add(EmailVerification(user_id=user_id, token_hash=hash_token(raw_token), expires_at=expires_at))
    return IssuedToken(raw_token=raw_token, expires_at=expires_at)


async def create_password_reset_token(db: AsyncSession, *, user_id: UUID) -> IssuedToken:
    raw_token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + PASSWORD_RESET_TOKEN_TTL
    db.add(PasswordReset(user_id=user_id, token_hash=hash_token(raw_token), expires_at=expires_at))
    return IssuedToken(raw_token=raw_token, expires_at=expires_at)


def is_expired(expires_at: datetime) -> bool:
    return _utc_now() > expires_at
