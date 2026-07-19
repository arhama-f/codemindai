from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_ai_orchestrator import AIProvider
from codemind_shared_types.schemas import RetrievedChunkDTO

from codemind_api.db import get_db
from codemind_api.main import create_app
from codemind_api.providers import get_real_ai_provider
from codemind_api.routers.indexing import get_redis_pool


async def _indexed_repository(client: AsyncClient, index_repository_directly, email: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Ask Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    job_id = job.json()["job_id"]
    await index_repository_directly(repository_id=repo_id, job_run_id=job_id)

    return org_id, repo_id


async def test_ask_before_indexing_is_conflict(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "ask-not-indexed@example.com", "password": "hunter2", "full_name": "Test"},
    )
    org = await client.post("/api/organizations", json={"name": "Ask Not Indexed Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask", json={"question": "where is divide?"}
    )
    assert response.status_code == 409


async def test_ask_about_divide_cites_math_ts(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "ask-divide@example.com")

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "where is the divide function?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["citations"]) >= 1
    top_citation = body["citations"][0]
    assert top_citation["file_path"] == "src/utils/math.ts"
    assert top_citation["start_line"] <= 14 <= top_citation["end_line"]
    assert "src/utils/math.ts:" in body["answer"]


async def test_ask_with_no_matching_keywords_returns_empty_citations(
    client: AsyncClient, index_repository_directly
):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "ask-no-match@example.com")

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "zzz nonexistent qqqq keyword xyzzy"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == []
    assert body["answer"] == "I couldn't find relevant code for that question in this repository."


async def test_ask_about_user_service_cites_class(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "ask-userservice@example.com")

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "how does createUser work in UserService?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert any(c["file_path"] == "src/services/userService.ts" for c in body["citations"])


class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


class _StubAIProvider(AIProvider):
    """A distinctive stand-in that isn't MockAIProvider's real template, so a
    test can prove /ask actually calls whatever get_real_ai_provider() returns
    instead of being hardcoded to MockAIProvider."""

    async def answer_repository_question(
        self, *, question: str, citations: list[RetrievedChunkDTO]
    ) -> str:
        return f"STUB ANSWER for: {question}"

    async def summarize_file(self, **kwargs):
        raise NotImplementedError

    async def summarize_directory(self, **kwargs):
        raise NotImplementedError

    async def identify_subsystems(self, **kwargs):
        raise NotImplementedError

    async def propose_fix(self, **kwargs):
        raise NotImplementedError

    async def summarize_pr_review(self, **kwargs):
        raise NotImplementedError


async def test_ask_uses_whatever_get_real_ai_provider_returns(
    db_session: AsyncSession, index_repository_directly
):
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    app.dependency_overrides[get_real_ai_provider] = lambda: _StubAIProvider()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_id, repo_id = await _indexed_repository(
            client, index_repository_directly, "ask-stub-provider@example.com"
        )
        response = await client.post(
            f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
            json={"question": "where is divide?"},
        )
        assert response.status_code == 200
        assert response.json()["answer"] == "STUB ANSWER for: where is divide?"
