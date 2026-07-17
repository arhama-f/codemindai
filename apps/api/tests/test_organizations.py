from httpx import AsyncClient


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    assert response.status_code == 201


async def test_create_organization_makes_creator_owner(client: AsyncClient):
    await _register(client, "owner@example.com")

    response = await client.post("/api/organizations", json={"name": "Acme Corp"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme Corp"
    assert body["slug"] == "acme-corp"

    listing = await client.get("/api/organizations")
    assert listing.status_code == 200
    orgs = listing.json()
    assert len(orgs) == 1
    assert orgs[0]["role"] == "owner"


async def test_duplicate_organization_name_gets_unique_slug(client: AsyncClient):
    await _register(client, "dup@example.com")

    first = await client.post("/api/organizations", json={"name": "Acme Corp"})
    second = await client.post("/api/organizations", json={"name": "Acme Corp"})

    assert first.json()["slug"] != second.json()["slug"]


async def test_non_member_cannot_view_organization(client: AsyncClient):
    await _register(client, "member-a@example.com")
    created = await client.post("/api/organizations", json={"name": "Private Org"})
    org_id = created.json()["id"]

    await client.post("/api/auth/logout")
    await _register(client, "member-b@example.com")

    response = await client.get(f"/api/organizations/{org_id}")
    assert response.status_code == 403


async def test_member_can_view_own_organization(client: AsyncClient):
    await _register(client, "solo@example.com")
    created = await client.post("/api/organizations", json={"name": "Solo Org"})
    org_id = created.json()["id"]

    response = await client.get(f"/api/organizations/{org_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Solo Org"
