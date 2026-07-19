import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import MockAIProvider
from codemind_github_client import MockGitHubWriteClient
from codemind_shared_types.schemas import PullRequestFileDTO

from codemind_api.db import get_db
from codemind_api.main import create_app
from codemind_api.providers import get_ai_provider_for_fix, get_github_write_client
from codemind_api.routers.indexing import get_redis_pool

DIVIDE_SOURCE = (
    "export function divide(a: number, b: number): number {\n"
    "  return a / b;\n"
    "}\n"
)


class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


@pytest_asyncio.fixture
async def client_with_write_client(db_session: AsyncSession):
    mock_write_client = MockGitHubWriteClient()
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    app.dependency_overrides[get_github_write_client] = lambda: mock_write_client
    app.dependency_overrides[get_ai_provider_for_fix] = lambda: MockAIProvider()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_write_client


async def _registered_org(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "PR Review Org"})
    return org.json()["id"]


async def test_review_without_target_configured_returns_400(client: AsyncClient, monkeypatch):
    from codemind_api.config import settings

    # Explicitly force "not configured" — don't rely on the ambient absence of
    # GITHUB_TARGET_OWNER/REPO, since a real .env (e.g. from a prior manual
    # verification step) may have set them for this process.
    monkeypatch.setattr(settings, "github_target_owner", None)
    monkeypatch.setattr(settings, "github_target_repo", None)

    org_id = await _registered_org(client, "pr-review-no-target@example.com")
    response = await client.post(f"/api/organizations/{org_id}/pr-reviews", json={"pr_number": 1})
    assert response.status_code == 400


async def test_review_posts_comment_for_finding_on_added_line(
    client_with_write_client, monkeypatch
):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")

    client, mock_write_client = client_with_write_client
    org_id = await _registered_org(client, "pr-review-added-line@example.com")

    mock_write_client.seed(owner="acme", repo="widgets", path="src/utils/math.ts", content=DIVIDE_SOURCE)
    mock_write_client.seed_pull_request(
        owner="acme",
        repo="widgets",
        pr_number=42,
        title="Add divide helper",
        head_sha="deadbeef",
        head_ref="feature/divide",
        base_ref="main",
        files=[
            PullRequestFileDTO(
                path="src/utils/math.ts",
                status="added",
                patch=(
                    "@@ -0,0 +1,3 @@\n"
                    "+export function divide(a: number, b: number): number {\n"
                    "+  return a / b;\n"
                    "+}"
                ),
            )
        ],
    )

    response = await client.post(f"/api/organizations/{org_id}/pr-reviews", json={"pr_number": 42})
    assert response.status_code == 201
    body = response.json()
    assert body["findings_count"] == 1
    assert body["comments_posted"] == 1
    assert body["status"] == "failure"  # unsafe-division is high severity
    assert body["review_url"] is not None
    assert body["pr_url"] == "https://github.com/acme/widgets/pull/42"

    assert len(mock_write_client.created_reviews) == 1
    review = mock_write_client.created_reviews[0]
    assert review["pr_number"] == 42
    assert review["comments"][0].path == "src/utils/math.ts"
    assert review["comments"][0].line == 2

    assert len(mock_write_client.created_commit_statuses) == 1
    commit_status = mock_write_client.created_commit_statuses[0]
    assert commit_status["state"] == "failure"
    assert commit_status["sha"] == "deadbeef"
    assert commit_status["context"] == "codemind-ai/pr-review"


async def test_review_skips_finding_outside_the_diff(client_with_write_client, monkeypatch):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")

    client, mock_write_client = client_with_write_client
    org_id = await _registered_org(client, "pr-review-outside-diff@example.com")

    mock_write_client.seed(owner="acme", repo="widgets", path="src/utils/math.ts", content=DIVIDE_SOURCE)
    mock_write_client.seed_pull_request(
        owner="acme",
        repo="widgets",
        pr_number=43,
        head_sha="cafefeed",
        head_ref="feature/unrelated",
        base_ref="main",
        # The division (line 2) is entirely unchanged context — only a new
        # trailing comment (line 4) is added — so the finding, which is still
        # detected internally, must not be commented on.
        files=[
            PullRequestFileDTO(
                path="src/utils/math.ts",
                status="modified",
                patch=(
                    "@@ -1,3 +1,4 @@\n"
                    " export function divide(a: number, b: number): number {\n"
                    "   return a / b;\n"
                    " }\n"
                    "+// trailing comment"
                ),
            )
        ],
    )

    response = await client.post(f"/api/organizations/{org_id}/pr-reviews", json={"pr_number": 43})
    assert response.status_code == 201
    body = response.json()
    assert body["findings_count"] == 0
    assert body["comments_posted"] == 0
    assert body["status"] == "success"
    assert body["review_url"] is None
    assert len(mock_write_client.created_reviews) == 0
    # A commit status is always set, even with zero findings.
    assert len(mock_write_client.created_commit_statuses) == 1
    assert mock_write_client.created_commit_statuses[0]["state"] == "success"


async def test_review_skips_non_ts_files(client_with_write_client, monkeypatch):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")

    client, mock_write_client = client_with_write_client
    org_id = await _registered_org(client, "pr-review-non-ts@example.com")

    mock_write_client.seed_pull_request(
        owner="acme",
        repo="widgets",
        pr_number=44,
        head_sha="feedface",
        head_ref="docs/update",
        base_ref="main",
        files=[
            PullRequestFileDTO(
                path="README.md",
                status="modified",
                patch="@@ -1,1 +1,2 @@\n context\n+added line",
            )
        ],
    )

    response = await client.post(f"/api/organizations/{org_id}/pr-reviews", json={"pr_number": 44})
    assert response.status_code == 201
    body = response.json()
    assert body["findings_count"] == 0
    assert body["comments_posted"] == 0
    assert body["status"] == "success"


async def test_get_pr_review_returns_it_by_id(client_with_write_client, monkeypatch):
    from codemind_api.config import settings

    monkeypatch.setattr(settings, "github_target_owner", "acme")
    monkeypatch.setattr(settings, "github_target_repo", "widgets")

    client, mock_write_client = client_with_write_client
    org_id = await _registered_org(client, "pr-review-get@example.com")

    mock_write_client.seed_pull_request(
        owner="acme",
        repo="widgets",
        pr_number=45,
        head_sha="0123456",
        head_ref="chore/noop",
        base_ref="main",
        files=[],
    )

    created = await client.post(f"/api/organizations/{org_id}/pr-reviews", json={"pr_number": 45})
    pr_review_id = created.json()["id"]

    response = await client.get(f"/api/organizations/{org_id}/pr-reviews/{pr_review_id}")
    assert response.status_code == 200
    assert response.json()["id"] == pr_review_id
    assert response.json()["pr_number"] == 45
