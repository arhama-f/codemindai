from httpx import AsyncClient
from sqlalchemy import select

from codemind_shared_types.models import File, RepositoryIndex, SymbolRelationship


async def _indexed_repository(client: AsyncClient, index_repository_directly, email: str) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Architecture Org"})
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


async def test_architecture_before_indexing_returns_empty(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "arch-not-indexed@example.com", "password": "hunter2", "full_name": "Test"},
    )
    org = await client.post("/api/organizations", json={"name": "Arch Not Indexed Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/architecture")
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": [], "subsystems": []}


async def test_architecture_returns_file_nodes_and_subsystems(
    client: AsyncClient, index_repository_directly
):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "arch-nodes@example.com")

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/architecture")
    assert response.status_code == 200
    body = response.json()

    assert len(body["nodes"]) == 8
    assert all(n["type"] == "file" for n in body["nodes"])

    subsystem_names = {s["name"] for s in body["subsystems"]}
    assert subsystem_names == {"utils", "models", "services", "components", "root"}

    utils_subsystem = next(s for s in body["subsystems"] if s["name"] == "utils")
    assert len(utils_subsystem["file_ids"]) == 3


async def test_architecture_includes_resolved_import_edge(
    client: AsyncClient, index_repository_directly
):
    org_id, repo_id = await _indexed_repository(client, index_repository_directly, "arch-edges@example.com")

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/architecture")
    body = response.json()

    nodes_by_id = {n["id"]: n for n in body["nodes"]}
    index_node = next(n for n in body["nodes"] if n["label"] == "src/index.ts")
    math_node = next(n for n in body["nodes"] if n["label"] == "src/utils/math.ts")

    resolved_edges = [e for e in body["edges"] if e["kind"] == "resolved"]
    assert any(
        e["source"] == index_node["id"] and e["target"] == math_node["id"] for e in resolved_edges
    )
    assert not any(n["type"] == "external" for n in nodes_by_id.values())


async def test_architecture_includes_external_edge_and_node(
    client: AsyncClient, index_repository_directly, db_session
):
    org_id, repo_id = await _indexed_repository(
        client, index_repository_directly, "arch-external@example.com"
    )

    index_result = await db_session.execute(
        select(RepositoryIndex).where(RepositoryIndex.repository_id == repo_id)
    )
    repository_index = index_result.scalar_one()

    file_result = await db_session.execute(
        select(File).where(
            File.repository_index_id == repository_index.id, File.path == "src/index.ts"
        )
    )
    index_file = file_result.scalar_one()

    db_session.add(
        SymbolRelationship(
            organization_id=org_id,
            repository_index_id=repository_index.id,
            from_file_id=index_file.id,
            to_file_id=None,
            relationship_type="imports",
            raw_specifier="react",
        )
    )
    await db_session.commit()

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/architecture")
    body = response.json()

    external_edges = [e for e in body["edges"] if e["kind"] == "external"]
    assert any(e["raw_specifier"] == "react" and e["target"] == "external" for e in external_edges)
    assert any(n["id"] == "external" and n["type"] == "external" for n in body["nodes"])
