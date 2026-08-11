from urllib.parse import parse_qs, urlparse

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import MockAIProvider
from codemind_email_provider import MockEmailProvider
from codemind_github_client import MockGitHubWriteClient
from codemind_oauth_client import MockOAuthProvider
from codemind_shared_types.models import GithubInstallation

from codemind_api.db import get_db
from codemind_api.main import create_app
from codemind_api.providers import (
    get_email_provider,
    get_github_repo_oauth_provider,
    get_github_write_client,
    get_oauth_provider,
    get_real_ai_provider,
)
from codemind_api.routers.indexing import get_redis_pool


class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Like the shared `client` fixture, but also overrides
    `get_github_repo_oauth_provider` — the repo-connect flow's own OAuth
    provider dependency, separate from login's `get_oauth_provider` — with a
    mock, since real GitHub OAuth credentials must never be exercised by the
    automated test suite."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    app.dependency_overrides[get_real_ai_provider] = lambda: MockAIProvider()
    app.dependency_overrides[get_github_write_client] = lambda: MockGitHubWriteClient()
    app.dependency_overrides[get_email_provider] = lambda: MockEmailProvider()
    app.dependency_overrides[get_oauth_provider] = lambda: MockOAuthProvider()
    app.dependency_overrides[get_github_repo_oauth_provider] = lambda: MockOAuthProvider()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _extract_state(location: str) -> str:
    return parse_qs(urlparse(location).query)["state"][0]


async def _register_and_create_org(client: AsyncClient, email: str, org_name: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": org_name})
    return created.json()["id"]


async def test_connect_start_redirects_and_state_encodes_org_id(client: AsyncClient):
    org_id = await _register_and_create_org(client, "start@example.com", "Start Org")

    response = await client.get(
        f"/api/organizations/{org_id}/github/connect/start", follow_redirects=False
    )

    assert response.status_code == 302
    assert "github_connect_state" in response.cookies
    state = _extract_state(response.headers["location"])
    assert state.startswith(f"{org_id}:")


async def test_connect_callback_creates_real_installation(
    client: AsyncClient, db_session: AsyncSession
):
    org_id = await _register_and_create_org(client, "callback@example.com", "Callback Org")

    start = await client.get(
        f"/api/organizations/{org_id}/github/connect/start", follow_redirects=False
    )
    state = _extract_state(start.headers["location"])

    callback = await client.get(
        "/api/organizations/github/connect/callback",
        params={"code": "any-code", "state": state},
        follow_redirects=False,
    )

    assert callback.status_code == 302
    assert callback.headers["location"].endswith(f"/orgs/{org_id}")

    # Asserted against `db_session` directly (not a follow-up API call) — the
    # real client's token resolver opens its own fresh SessionLocal()
    # connection, which can't see writes made inside this test's savepoint
    # transaction until it commits (same quirk documented on the
    # `real_db_session` fixture for the SSE test).
    result = await db_session.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation = result.scalar_one()
    assert installation.provider == "github"
    assert installation.access_token == "mock-access-token"

    # The response models (InstallationResponse/RepositoryListingResponse)
    # never declare an access_token field — confirmed statically here rather
    # than via a live call, for the same cross-connection reason above.
    from codemind_api.routers.github import InstallationResponse, RepositoryListingResponse

    assert "access_token" not in InstallationResponse.model_fields
    assert "access_token" not in RepositoryListingResponse.model_fields


async def test_connect_callback_rejects_state_for_org_current_user_cant_access(
    client: AsyncClient,
):
    org_id = await _register_and_create_org(client, "victim@example.com", "Victim Org")

    start = await client.get(
        f"/api/organizations/{org_id}/github/connect/start", follow_redirects=False
    )
    state = _extract_state(start.headers["location"])

    # A different session now reuses the same (cookie, state) pair — the state
    # cookie check alone would pass, so the explicit org-membership check must
    # be what rejects this.
    await client.post(
        "/api/auth/register",
        json={"email": "attacker@example.com", "password": "hunter2", "full_name": "Attacker"},
    )

    callback = await client.get(
        "/api/organizations/github/connect/callback",
        params={"code": "any-code", "state": state},
        follow_redirects=False,
    )

    assert callback.status_code == 403


async def test_connect_callback_with_mismatched_state_is_bad_request(client: AsyncClient):
    org_id = await _register_and_create_org(client, "mismatch@example.com", "Mismatch Org")

    await client.get(f"/api/organizations/{org_id}/github/connect/start", follow_redirects=False)

    response = await client.get(
        "/api/organizations/github/connect/callback",
        params={"code": "any-code", "state": f"{org_id}:wrong-nonce"},
        follow_redirects=False,
    )

    assert response.status_code == 400
