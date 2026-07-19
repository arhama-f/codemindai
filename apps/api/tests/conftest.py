import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind_test"
os.environ["REDIS_URL"] = "redis://localhost:6380/0"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import MockAIProvider
from codemind_github_client import MockGitHubWriteClient

from codemind_api.db import SessionLocal, engine, get_db
from codemind_api.main import create_app
from codemind_api.providers import get_real_ai_provider, get_github_write_client
from codemind_api.routers.indexing import get_redis_pool


class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    """Stands in for the real arq redis pool in API-level tests — enqueue
    wiring is exercised here, while the indexing pipeline itself is tested
    directly (without going through arq/redis) in apps/worker/tests."""

    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


@pytest_asyncio.fixture
async def db_session():
    # The engine is a module-level singleton shared with the running app, but each
    # pytest-asyncio test gets its own event loop; disposing first forces the pool
    # to open fresh connections bound to the current loop instead of a stale one.
    await engine.dispose()
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


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    # Force mocks regardless of real credentials in the environment/.env —
    # automated tests must never call the real Claude or GitHub APIs. Tests
    # that specifically need a seeded MockGitHubWriteClient (e.g. publish
    # staleness checks) override get_github_write_client again themselves.
    app.dependency_overrides[get_real_ai_provider] = lambda: MockAIProvider()
    app.dependency_overrides[get_github_write_client] = lambda: MockGitHubWriteClient()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def real_db_session():
    """A session that really commits (unlike `db_session`'s rollback-only
    savepoint), needed for the SSE test: the streaming endpoint intentionally
    polls via fresh `SessionLocal()` connections, which can't see writes made
    inside another connection's uncommitted transaction."""
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def index_repository_directly(db_session: AsyncSession):
    """Runs the real indexing pipeline synchronously against the test's own
    `db_session`, bypassing the real redis-backed arq worker — used to set up
    an already-indexed repository fixture within a single test transaction."""
    from codemind_ai_orchestrator import MockAIProvider
    from codemind_embedding_provider import get_default_provider
    from codemind_github_client import MockGitHubClient
    from codemind_worker.tasks.index_repository import index_repository

    from codemind_api.config import settings

    class _SingleSessionContextManager:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *exc_info):
            return False

    ctx = {
        "db_sessionmaker": lambda: _SingleSessionContextManager(),
        "github_client": MockGitHubClient(demo_repo_root=settings.demo_repo_root),
        "ai_provider": MockAIProvider(),
        "embedding_provider": get_default_provider(),
    }

    async def _run(*, repository_id: str, job_run_id: str) -> None:
        await index_repository(ctx, repository_id=repository_id, job_run_id=job_run_id)

    return _run


@pytest_asyncio.fixture
async def analyze_repository_directly(db_session: AsyncSession):
    """Runs the real analysis pipeline synchronously against the test's own
    `db_session`, bypassing the real redis-backed arq worker — mirrors
    `index_repository_directly` above."""
    from codemind_worker.tasks.analyze_repository import analyze_repository

    class _SingleSessionContextManager:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *exc_info):
            return False

    ctx = {"db_sessionmaker": lambda: _SingleSessionContextManager()}

    async def _run(*, repository_id: str, job_run_id: str) -> None:
        await analyze_repository(ctx, repository_id=repository_id, job_run_id=job_run_id)

    return _run
