import os
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from codemind_ai_orchestrator import MockAIProvider
from codemind_embedding_provider import get_default_provider
from codemind_github_client import MockGitHubClient

REPO_ROOT = Path(__file__).resolve().parents[4]

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6380/0")
DEMO_REPO_ROOT = os.environ.get("DEMO_REPO_ROOT", str(REPO_ROOT / "fixtures" / "demo-repo"))


async def startup(ctx: dict) -> None:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    ctx["engine"] = engine
    ctx["db_sessionmaker"] = async_sessionmaker(engine, expire_on_commit=False)
    ctx["github_client"] = MockGitHubClient(demo_repo_root=DEMO_REPO_ROOT)
    ctx["ai_provider"] = MockAIProvider()
    ctx["embedding_provider"] = get_default_provider()


async def shutdown(ctx: dict) -> None:
    await ctx["engine"].dispose()
