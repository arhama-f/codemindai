from httpx import AsyncClient


async def _org_with_repo(client: AsyncClient, email: str, org_name: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": org_name})
    org_id = created.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    return org_id, repo.json()["id"]


async def test_start_indexing_enqueues_job(client: AsyncClient):
    org_id, repo_id = await _org_with_repo(client, "index-start@example.com", "Index Start Org")

    response = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert job_id

    job_response = await client.get(f"/api/organizations/{org_id}/jobs/{job_id}")
    assert job_response.status_code == 200
    body = job_response.json()
    assert body["status"] == "queued"
    assert body["progress_percent"] == 0


async def test_start_indexing_unknown_repository_is_not_found(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "unknown-index@example.com", "password": "hunter2", "full_name": "Test"},
    )
    created = await client.post("/api/organizations", json={"name": "Unknown Index Org"})
    org_id = created.json()["id"]
    fake_repo_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(f"/api/organizations/{org_id}/repositories/{fake_repo_id}/index")
    assert response.status_code == 404


async def test_get_job_not_found(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "no-job@example.com", "password": "hunter2", "full_name": "Test"},
    )
    created = await client.post("/api/organizations", json={"name": "No Job Org"})
    org_id = created.json()["id"]
    fake_job_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/organizations/{org_id}/jobs/{fake_job_id}")
    assert response.status_code == 404
