from httpx import AsyncClient


async def _org_with_github_connected(client: AsyncClient, email: str, org_name: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": org_name})
    org_id = created.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    return org_id


async def test_add_repository_requires_github_connected(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "no-github@example.com", "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": "No Github Org"})
    org_id = created.json()["id"]

    response = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    assert response.status_code == 409


async def test_add_repository_and_list(client: AsyncClient):
    org_id = await _org_with_github_connected(client, "add-repo@example.com", "Add Repo Org")

    add_response = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    assert add_response.status_code == 201
    body = add_response.json()
    assert body["full_name"] == "codemind-demo/todo-app-ts"
    assert body["latest_index_status"] is None

    listing = await client.get(f"/api/organizations/{org_id}/repositories")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_add_unknown_repository_is_not_found(client: AsyncClient):
    org_id = await _org_with_github_connected(client, "unknown-repo@example.com", "Unknown Repo Org")

    response = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "does-not-exist"}
    )
    assert response.status_code == 404


async def test_other_org_cannot_see_repositories(client: AsyncClient):
    org_id = await _org_with_github_connected(client, "owner-repo@example.com", "Owner Repo Org")
    await client.post(f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"})

    await client.post("/api/auth/logout")
    await client.post(
        "/api/auth/register",
        json={"email": "outsider@example.com", "password": "hunter2", "full_name": "Outsider"},
    )

    response = await client.get(f"/api/organizations/{org_id}/repositories")
    assert response.status_code == 403
