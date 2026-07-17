from httpx import AsyncClient


async def _indexed_repository(client: AsyncClient, index_repository_directly, email: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Files Org"})
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


async def test_list_files_returns_indexed_files(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "files-list@example.com")

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/files")
    assert response.status_code == 200
    paths = {f["path"] for f in response.json()}
    assert paths == {
        "src/index.ts",
        "src/utils/math.ts",
        "src/utils/string.ts",
        "src/models/user.ts",
        "src/services/userService.ts",
        "src/components/UserCard.tsx",
    }


async def test_list_files_before_indexing_is_empty(client: AsyncClient, index_repository_directly):
    await client.post(
        "/api/auth/register",
        json={"email": "not-indexed@example.com", "password": "hunter2", "full_name": "Test"},
    )
    org = await client.post("/api/organizations", json={"name": "Not Indexed Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/files")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_file_detail_includes_symbols(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "file-detail@example.com")

    files_response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/files")
    math_file = next(f for f in files_response.json() if f["path"] == "src/utils/math.ts")

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/files/{math_file['id']}"
    )
    assert response.status_code == 200
    body = response.json()
    assert "export function divide" in body["content"]
    symbol_names = {s["name"] for s in body["symbols"]}
    assert symbol_names == {"add", "subtract", "multiply", "divide"}


async def test_search_symbols_case_insensitive_partial_match(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "symbol-search@example.com")

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols", params={"query": "divi"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["name"] == "divide"
    assert results[0]["file_path"] == "src/utils/math.ts"


async def test_search_symbols_without_query_returns_all(client: AsyncClient, index_repository_directly):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "symbol-all@example.com")

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/symbols")
    assert response.status_code == 200
    assert len(response.json()) == 14


async def test_get_summary_returns_repository_and_directory_summaries(
    client: AsyncClient, index_repository_directly
):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "summary@example.com")

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["repository_summary"] is not None
    assert len(body["directories"]) >= 1


async def test_get_summary_before_indexing_returns_nulls(client: AsyncClient, index_repository_directly):
    await client.post(
        "/api/auth/register",
        json={"email": "no-summary@example.com", "password": "hunter2", "full_name": "Test"},
    )
    org = await client.post("/api/organizations", json={"name": "No Summary Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["repository_summary"] is None
    assert body["directories"] == []
