import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from codemind_ai_orchestrator import MockAIProvider
from codemind_embedding_provider import get_default_provider
from codemind_github_client import MockGitHubClient, OAuthTokenGitHubClient
from codemind_shared_types.models import GithubInstallation

REPO_ROOT = Path(__file__).resolve().parents[4]

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6380/0")
DEMO_REPO_ROOT = os.environ.get("DEMO_REPO_ROOT", str(REPO_ROOT / "fixtures" / "demo-repo"))


async def startup(ctx: dict) -> None:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    ctx["engine"] = engine
    ctx["db_sessionmaker"] = sessionmaker
    ctx["github_client"] = MockGitHubClient(demo_repo_root=DEMO_REPO_ROOT)

    async def _resolve_access_token(external_installation_id: str) -> str:
        async with sessionmaker() as session:
            result = await session.execute(
                select(GithubInstallation.access_token).where(
                    GithubInstallation.external_installation_id == external_installation_id
                )
            )
            token = result.scalar_one_or_none()
        if not token:
            raise RuntimeError(f"No stored GitHub access token for installation {external_installation_id}")
        return token

    ctx["real_github_client"] = OAuthTokenGitHubClient(resolve_access_token=_resolve_access_token)
    ctx["ai_provider"] = MockAIProvider()
    ctx["embedding_provider"] = get_default_provider()


async def shutdown(ctx: dict) -> None:
    await ctx["engine"].dispose()
