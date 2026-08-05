from functools import lru_cache

from codemind_ai_orchestrator import AIProvider, ClaudeAIProvider, MockAIProvider
from codemind_email_provider import EmailProvider, MockEmailProvider, ResendEmailProvider
from codemind_embedding_provider import EmbeddingProvider, get_default_provider
from codemind_github_client import (
    GitHubClient,
    GitHubWriteClient,
    MockGitHubClient,
    MockGitHubWriteClient,
    PATGitHubWriteClient,
)
from codemind_oauth_client import GitHubOAuthProvider, GoogleOAuthProvider, OAuthProvider
from fastapi import HTTPException, status

from codemind_api.config import settings


@lru_cache
def get_github_client() -> GitHubClient:
    return MockGitHubClient(demo_repo_root=settings.demo_repo_root)


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
