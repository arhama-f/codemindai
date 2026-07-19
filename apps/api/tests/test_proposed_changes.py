import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import MockAIProvider

from codemind_api.db import get_db
from codemind_api.main import create_app
from codemind_api.providers import get_real_ai_provider, get_github_write_client
from codemind_api.routers.indexing import get_redis_pool
from codemind_github_client import MockGitHubWriteClient


class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


@pytest_asyncio.fixture
async def client_with_write_client(db_session: AsyncSession):
    """Like the shared `client` fixture, but also overrides
    `get_github_write_client` with a mock instance the test can seed and
    inspect — needed for the publish endpoint's staleness check and PR/branch
    assertions."""
    mock_write_client = MockGitHubWriteClient()
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    app.dependency_overrides[get_github_write_client] = lambda: mock_write_client
    # Force the mock AI provider regardless of real credentials in the
    # environment/.env — automated tests must never call the real Claude API.
    app.dependency_overrides[get_real_ai_provider] = lambda: MockAIProvider()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_write_client


async def _indexed_and_analyzed_repository(
    client: AsyncClient, index_repository_directly, analyze_repository_directly, email: str
) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Proposed Changes Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    index_job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    await index_repository_directly(repository_id=repo_id, job_run_id=index_job.json()["job_id"])

    analyze_response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/analyses"
    )
    analyze_job_id = analyze_response.json()["job_id"]
    await analyze_repository_directly(repository_id=repo_id, job_run_id=analyze_job_id)

    return org_id, repo_id


async def _get_finding_id(client: AsyncClient, org_id: str, repo_id: str, check_id: str) -> str:
    listing = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/findings")
    finding = next(f for f in listing.json() if f["check_id"] == check_id)
    return finding["id"]


async def _file_content(client: AsyncClient, org_id: str, repo_id: str, file_path: str) -> str:
    listing = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/files")
    file_entry = next(f for f in listing.json() if f["path"] == file_path)
    detail = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/files/{file_entry['id']}"
    )
    return detail.json()["content"]


async def test_propose_fix_creates_a_draft_proposed_change(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "propose-fix@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["generated_by"] == "mock"
    assert "unsafe-division" in body["explanation"]
    assert body["updated_content"]
    assert body["test_file_path"] is None
    assert body["pr_url"] is None


async def test_get_proposed_change_returns_it_by_id(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "get-proposed@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")

    created = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    proposed_change_id = created.json()["id"]

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}"
    )
    assert response.status_code == 200
    assert response.json()["id"] == proposed_change_id


async def test_publish_without_target_configured_returns_400(
    client: AsyncClient, index_repository_directly, analyze_repository_directly, monkeypatch
):
    from codemind_api.config import settings

    # Explicitly force "not configured" — don't rely on the ambient absence of
    # GITHUB_TARGET_OWNER/REPO, since a real .env (e.g. from a prior manual
    # verification step) may have set them for this process.
    monkeypatch.setattr(settings, "github_target_owner", None)
    monkeypatch.setattr(settings, "github_target_repo", None)

    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "publish-no-target@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")
    created = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    proposed_change_id = created.json()["id"]

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}/publish"
    )
    assert response.status_code == 400


async def test_publish_succeeds_with_matching_remote_content(
    client_with_write_client, index_repository_directly, analyze_repository_directly, monkeypatch
):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")
    monkeypatch.setattr(settings, "github_target_base_branch", "main")
    monkeypatch.setattr(settings, "github_target_path_prefix", "")

    client, mock_write_client = client_with_write_client
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "publish-ok@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")
    created = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    proposed_change_id = created.json()["id"]

    detail = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}"
    )
    file_path = detail.json()["file_path"]
    file_content = await _file_content(client, org_id, repo_id, file_path)

    # Seed the mock remote with the exact same content the fix was generated
    # from, so the staleness check passes rather than returning 409.
    mock_write_client.seed(owner="acme", repo="widgets", path=file_path, content=file_content)

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}/publish"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pr_number"] == 1
    assert body["pr_url"] == "https://github.com/acme/widgets/pull/1"
    assert len(mock_write_client.created_branches) == 1
    assert len(mock_write_client.created_pull_requests) == 1

    detail_after = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}"
    )
    assert detail_after.json()["status"] == "published"
    assert detail_after.json()["pr_url"] == body["pr_url"]


async def test_publish_twice_returns_409(
    client_with_write_client, index_repository_directly, analyze_repository_directly, monkeypatch
):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")
    monkeypatch.setattr(settings, "github_target_base_branch", "main")
    monkeypatch.setattr(settings, "github_target_path_prefix", "")

    client, mock_write_client = client_with_write_client
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "publish-twice@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")
    created = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    proposed_change_id = created.json()["id"]

    detail = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}"
    )
    file_path = detail.json()["file_path"]
    file_content = await _file_content(client, org_id, repo_id, file_path)
    mock_write_client.seed(owner="acme", repo="widgets", path=file_path, content=file_content)

    first = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}/publish"
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}/publish"
    )
    assert second.status_code == 409


async def test_publish_with_stale_remote_content_returns_409(
    client_with_write_client, index_repository_directly, analyze_repository_directly, monkeypatch
):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")
    monkeypatch.setattr(settings, "github_target_base_branch", "main")
    monkeypatch.setattr(settings, "github_target_path_prefix", "")

    client, mock_write_client = client_with_write_client
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "publish-stale@example.com"
    )
    finding_id = await _get_finding_id(client, org_id, repo_id, "unsafe-division")
    created = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/propose-fix"
    )
    proposed_change_id = created.json()["id"]

    detail = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}"
    )
    file_path = detail.json()["file_path"]

    # Seed the mock remote with content that has diverged from what the fix
    # was generated from.
    mock_write_client.seed(
        owner="acme", repo="widgets", path=file_path, content="// this content has diverged upstream\n"
    )

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/proposed-changes/{proposed_change_id}/publish"
    )
    assert response.status_code == 409
    assert len(mock_write_client.created_branches) == 0
