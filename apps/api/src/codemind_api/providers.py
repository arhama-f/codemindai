from functools import lru_cache

from codemind_ai_orchestrator import AIProvider, ClaudeAIProvider, MockAIProvider
from codemind_embedding_provider import EmbeddingProvider, get_default_provider
from codemind_github_client import (
    GitHubClient,
    GitHubWriteClient,
    MockGitHubClient,
    MockGitHubWriteClient,
    PATGitHubWriteClient,
)

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
def get_ai_provider_for_fix() -> AIProvider:
    """Real Claude-backed provider only when ANTHROPIC_API_KEY is configured
    — otherwise the deterministic mock. Separate from get_ai_provider()
    because ClaudeAIProvider only implements propose_fix (round 4 scope)."""
    if settings.anthropic_api_key:
        return ClaudeAIProvider(api_key=settings.anthropic_api_key)
    return MockAIProvider()
