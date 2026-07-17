from httpx import AsyncClient


async def _indexed_repository(client: AsyncClient, index_repository_directly, email: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Ask Embeddings Org"})
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


async def test_semantically_related_question_with_no_keyword_overlap_finds_divide(
    client: AsyncClient, index_repository_directly
):
    """Proves retrieval is genuinely semantic, not just lexical: this question
    shares zero literal words with "divide"/"function"/"math", so only real
    embedding similarity (not the ILIKE keyword-scoring fallback) can find it."""
    org_id, repo_id = await _indexed_repository(
        client, index_repository_directly, "ask-embed-divide@example.com"
    )

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "how do I split a number into pieces?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["file_path"] == "src/utils/math.ts"
    assert body["citations"][0]["start_line"] <= 14 <= body["citations"][0]["end_line"]


async def test_nonsense_question_still_returns_empty_citations_with_embeddings_enabled(
    client: AsyncClient, index_repository_directly
):
    """Regression guard: a real embedding model never says "no match" (every
    chunk has *some* similarity) — this asserts the distance cutoff still
    filters those out rather than always returning the 3 least-dissimilar
    chunks."""
    org_id, repo_id = await _indexed_repository(
        client, index_repository_directly, "ask-embed-nonsense@example.com"
    )

    response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "what does the weather look like tomorrow in paris"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == []
