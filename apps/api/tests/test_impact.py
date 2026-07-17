from httpx import AsyncClient


async def _indexed_repository(client: AsyncClient, index_repository_directly, email: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Impact Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    await index_repository_directly(repository_id=repo_id, job_run_id=job.json()["job_id"])

    return org_id, repo_id


async def test_impact_of_divide_shows_index_ts_as_direct_dependent(
    client: AsyncClient, index_repository_directly
):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "impact-divide@example.com")

    symbols_response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols", params={"query": "divide"}
    )
    divide_symbol = next(s for s in symbols_response.json() if s["name"] == "divide")

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols/{divide_symbol['id']}/impact"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol_name"] == "divide"
    assert body["file_path"] == "src/utils/math.ts"

    direct_paths = {f["file_path"] for f in body["direct_dependent_files"]}
    assert "src/index.ts" in direct_paths

    direct_index = next(f for f in body["direct_dependent_files"] if f["file_path"] == "src/index.ts")
    assert direct_index["confidence"] == "confirmed_static"


async def test_impact_of_unused_symbol_has_no_dependents(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "impact-unused@example.com")

    symbols_response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols", params={"query": "multiply"}
    )
    multiply_symbol = next(s for s in symbols_response.json() if s["name"] == "multiply")

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols/{multiply_symbol['id']}/impact"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["direct_dependent_files"] == []
    assert body["transitive_dependent_files"] == []


async def test_impact_of_unknown_symbol_is_not_found(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "impact-404@example.com")

    fake_symbol_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols/{fake_symbol_id}/impact"
    )
    assert response.status_code == 404
