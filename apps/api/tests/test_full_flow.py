from httpx import AsyncClient


async def test_full_onboarding_to_ask_flow(client: AsyncClient, index_repository_directly):
    """End-to-end vertical slice: register -> create org -> connect mock GitHub
    -> select the demo repo -> run indexing -> poll status ready -> ask a
    question -> get an answer with a citation."""

    # 1. Register
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "e2e@example.com", "password": "hunter2", "full_name": "E2E Tester"},
    )
    assert register_response.status_code == 201

    # 2. Create organization
    org_response = await client.post("/api/organizations", json={"name": "E2E Org"})
    assert org_response.status_code == 201
    org_id = org_response.json()["id"]

    # 3. Connect mock GitHub
    connect_response = await client.post(f"/api/organizations/{org_id}/github/connect")
    assert connect_response.status_code == 200
    assert connect_response.json()["account_login"] == "codemind-demo"

    # 4. List and select the demo repository
    available_response = await client.get(f"/api/organizations/{org_id}/github/repositories")
    assert available_response.status_code == 200
    available_repos = available_response.json()
    assert len(available_repos) == 1
    external_repo_id = available_repos[0]["external_repo_id"]

    add_response = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": external_repo_id}
    )
    assert add_response.status_code == 201
    repo_id = add_response.json()["id"]
    assert add_response.json()["latest_index_status"] is None

    # 5. Queue indexing
    index_response = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    assert index_response.status_code == 202
    job_id = index_response.json()["job_id"]

    job_before = await client.get(f"/api/organizations/{org_id}/jobs/{job_id}")
    assert job_before.json()["status"] == "queued"

    # Run the pipeline (bypassing the real redis-backed worker, as in the
    # other integration tests in this suite).
    await index_repository_directly(repository_id=repo_id, job_run_id=job_id)

    # 6. Poll status ready
    job_after = await client.get(f"/api/organizations/{org_id}/jobs/{job_id}")
    assert job_after.status_code == 200
    assert job_after.json()["status"] == "completed"
    assert job_after.json()["progress_percent"] == 100

    repo_detail = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}")
    assert repo_detail.json()["latest_index_status"] == "completed"

    # Repository summary and symbol search should now reflect the indexed repo.
    summary_response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/summary")
    assert summary_response.json()["repository_summary"] is not None

    symbols_response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/symbols", params={"query": "UserService"}
    )
    assert any(s["name"] == "UserService" for s in symbols_response.json())

    # 7. Ask a question and get a cited answer
    ask_response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/ask",
        json={"question": "Where is the divide function and could it fail?"},
    )
    assert ask_response.status_code == 200
    ask_body = ask_response.json()
    assert len(ask_body["citations"]) >= 1
    assert ask_body["citations"][0]["file_path"] == "src/utils/math.ts"
    assert "src/utils/math.ts:" in ask_body["answer"]
