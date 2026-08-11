from functools import lru_cache

from codemind_ai_orchestrator import AIProvider, ClaudeAIProvider, MockAIProvider
from codemind_email_provider import EmailProvider, MockEmailProvider, ResendEmailProvider
from codemind_embedding_provider import EmbeddingProvider, get_default_provider
from codemind_github_client import (
    GitHubClient,
    GitHubWriteClient,
    MockGitHubClient,
    MockGitHubWriteClient,
    OAuthTokenGitHubClient,
    PATGitHubWriteClient,
)
from codemind_oauth_client import GitHubOAuthProvider, GoogleOAuthProvider, OAuthProvider
from fastapi import HTTPException, status
from sqlalchemy import select

from codemind_api.config import settings
from codemind_api.db import SessionLocal
from codemind_shared_types.models import GithubInstallation


@lru_cache
def get_github_client() -> GitHubClient:
    return MockGitHubClient(demo_repo_root=settings.demo_repo_root)


async def _resolve_installation_access_token(external_installation_id: str) -> str:
    async with SessionLocal() as session:
        result = await session.execute(
            select(GithubInstallation.access_token).where(
                GithubInstallation.external_installation_id == external_installation_id
            )
        )
        token = result.scalar_one_or_none()
    if not token:
        raise RuntimeError(f"No stored GitHub access token for installation {external_installation_id}")
    return token


@lru_cache
def get_real_github_client() -> GitHubClient:
    return OAuthTokenGitHubClient(resolve_access_token=_resolve_installation_access_token)


def get_github_client_for_installation(installation: GithubInstallation) -> GitHubClient:
    """Real installations (provider="github", created by the OAuth connect
    callback) use OAuthTokenGitHubClient; legacy/demo installations
    (provider="mock", from the old POST /connect route) keep using the
    mock — dispatch is per-row, not per-process."""
    if installation.provider == "github":
        return get_real_github_client()
    return get_github_client()


def get_github_repo_oauth_provider() -> GitHubOAuthProvider:
    """Same GITHUB_OAUTH_CLIENT_ID/SECRET as login, different redirect_uri —
    GitHub requires an exact match against the OAuth App's registered
    callback URL, so repo-connect needs its own fixed callback distinct
    from login's. 501s if unconfigured, same as get_oauth_provider."""
    if not (settings.github_oauth_client_id and settings.github_oauth_client_secret):
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth is not configured")
    return GitHubOAuthProvider(
        client_id=settings.github_oauth_client_id,
        client_secret=settings.github_oauth_client_secret,
        redirect_uri=f"{settings.api_origin}/api/organizations/github/connect/callback",
    )


@lru_cache
def get_ai_provider() -> AIProvider:
    return MockAIProvider()


def get_embedding_provider() -> EmbeddingProvider:
    return get_default_provider()


@lru_cache
def get_github_write_client() -> GitHubWriteClient:
    """Real PAT-backed client only when GITHUB_PAT is configured — otherwise
    an in-memory mock. Never real by default; see docs/architecture.md."""
    if settings.github_pat:
        return PATGitHubWriteClient(token=settings.github_pat)
    return MockGitHubWriteClient()


@lru_cache
def get_real_ai_provider() -> AIProvider:
    """Real Claude-backed provider only when ANTHROPIC_API_KEY is configured
    — otherwise the deterministic mock. Separate from get_ai_provider() because
    ClaudeAIProvider only implements propose_fix, summarize_pr_review, and
    answer_repository_question — the three places CodeMind generates
    user-facing text from a real model rather than a template."""
    if settings.anthropic_api_key:
        return ClaudeAIProvider(api_key=settings.anthropic_api_key)
    return MockAIProvider()


@lru_cache
def get_email_provider() -> EmailProvider:
    """Real Resend-backed provider only when RESEND_API_KEY is configured —
    otherwise the in-memory mock. Never real by default."""
    if settings.resend_api_key:
        return ResendEmailProvider(
            api_key=settings.resend_api_key, from_email=settings.resend_from_email
        )
    return MockEmailProvider()


def get_oauth_provider(provider: str) -> OAuthProvider:
    """Real Google/GitHub OAuth provider only when that provider's client
    id/secret are configured — otherwise 501, since there's no honest mock
    for a real login redirect. `provider` is validated by the router's path
    literal, not user input, so an unknown value here is a programming error."""
    redirect_uri = f"{settings.api_origin}/api/auth/oauth/{provider}/callback"
    if provider == "google":
        if settings.google_client_id and settings.google_client_secret:
            return GoogleOAuthProvider(
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                redirect_uri=redirect_uri,
            )
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth is not configured")
    if provider == "github":
        if settings.github_oauth_client_id and settings.github_oauth_client_secret:
            return GitHubOAuthProvider(
                client_id=settings.github_oauth_client_id,
                client_secret=settings.github_oauth_client_secret,
                redirect_uri=redirect_uri,
            )
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth is not configured")
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown OAuth provider: {provider}")
