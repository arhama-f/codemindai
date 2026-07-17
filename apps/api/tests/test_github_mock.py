from httpx import AsyncClient


async def _register_and_create_org(client: AsyncClient, email: str, org_name: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": org_name})
    return created.json()["id"]


async def test_connect_creates_installation(client: AsyncClient):
    org_id = await _register_and_create_org(client, "connect@example.com", "Connect Org")

    response = await client.post(f"/api/organizations/{org_id}/github/connect")
    assert response.status_code == 200
    body = response.json()
    assert body["account_login"] == "codemind-demo"


async def test_connect_is_idempotent(client: AsyncClient):
    org_id = await _register_and_create_org(client, "idempotent@example.com", "Idempotent Org")

    first = await client.post(f"/api/organizations/{org_id}/github/connect")
    second = await client.post(f"/api/organizations/{org_id}/github/connect")

    assert first.json()["installation_id"] == second.json()["installation_id"]


async def test_list_repositories_returns_fixture_repo(client: AsyncClient):
    org_id = await _register_and_create_org(client, "list-repos@example.com", "List Repos Org")
    await client.post(f"/api/organizations/{org_id}/github/connect")

    response = await client.get(f"/api/organizations/{org_id}/github/repositories")
    assert response.status_code == 200
    repos = response.json()
    assert len(repos) == 1
    assert repos[0]["external_repo_id"] == "demo-1"
    assert repos[0]["full_name"] == "codemind-demo/todo-app-ts"


async def test_list_repositories_before_connect_is_empty(client: AsyncClient):
    org_id = await _register_and_create_org(client, "not-connected@example.com", "Not Connected Org")

    response = await client.get(f"/api/organizations/{org_id}/github/repositories")
    assert response.status_code == 200
    assert response.json() == []
