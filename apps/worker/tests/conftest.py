import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind_test"
)

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from codemind_ai_orchestrator import MockAIProvider
from codemind_embedding_provider import get_default_provider
from codemind_github_client import MockGitHubClient
from codemind_worker.deps import DEMO_REPO_ROOT, DATABASE_URL


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    connection = await engine.connect()
    trans = await connection.begin()
    session = AsyncSession(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def worker_ctx(db_session: AsyncSession):
    class _SingleSessionContextManager:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *exc_info):
            return False

    def sessionmaker():
        return _SingleSessionContextManager()

    return {
        "db_sessionmaker": sessionmaker,
        "github_client": MockGitHubClient(demo_repo_root=DEMO_REPO_ROOT),
        "ai_provider": MockAIProvider(),
        "embedding_provider": get_default_provider(),
    }
