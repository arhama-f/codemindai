from functools import lru_cache

from codemind_ai_orchestrator import AIProvider, MockAIProvider
from codemind_embedding_provider import EmbeddingProvider, get_default_provider
from codemind_github_client import GitHubClient, MockGitHubClient

from codemind_api.config import settings


@lru_cache
def get_github_client() -> GitHubClient:
    return MockGitHubClient(demo_repo_root=settings.demo_repo_root)


@lru_cache
def get_ai_provider() -> AIProvider:
    return MockAIProvider()


def get_embedding_provider() -> EmbeddingProvider:
    return get_default_provider()
