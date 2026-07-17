from httpx import AsyncClient


async def _indexed_and_analyzed_repository(
    client: AsyncClient, index_repository_directly, analyze_repository_directly, email: str
) -> tuple[str, str]:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    org = await client.post("/api/organizations", json={"name": "Findings Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    index_job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    await index_repository_directly(
        repository_id=repo_id, job_run_id=index_job.json()["job_id"]
    )

    analyze_response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/analyses"
    )
    assert analyze_response.status_code == 202
    analyze_job_id = analyze_response.json()["job_id"]
    await analyze_repository_directly(repository_id=repo_id, job_run_id=analyze_job_id)

    return org_id, repo_id


async def test_start_analysis_before_indexing_fails(client: AsyncClient, analyze_repository_directly):
    await client.post(
        "/api/auth/register",
        json={"email": "analyze-not-indexed@example.com", "password": "hunter2", "full_name": "Test"},
    )
    org = await client.post("/api/organizations", json={"name": "Analyze Not Indexed Org"})
    org_id = org.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    response = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/analyses")
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    raised = False
    try:
        await analyze_repository_directly(repository_id=repo_id, job_run_id=job_id)
    except ValueError:
        raised = True
    assert raised

    findings_response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings"
    )
    assert findings_response.status_code == 200
    assert findings_response.json() == []


async def test_list_findings_returns_all_nine_planted_issues(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "findings-list@example.com"
    )

    response = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/findings")
    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 9
    assert all(f["status"] == "open" for f in findings)

    check_ids = {f["check_id"] for f in findings}
    assert "unsafe-division" in check_ids
    assert "hardcoded-secret" in check_ids
    assert "nested-loop-quadratic" in check_ids


async def test_list_findings_filters_by_category(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "findings-filter@example.com"
    )

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings",
        params={"category": "security"},
    )
    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 3
    assert all(f["category"] == "security" for f in findings)


async def test_get_finding_detail_includes_explanation_and_evidence(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "findings-detail@example.com"
    )

    listing = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/findings")
    division_finding = next(f for f in listing.json() if f["check_id"] == "unsafe-division")

    response = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{division_finding['id']}"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["explanation"]
    assert body["recommended_fix"]
    assert len(body["evidence"]) >= 1
    assert body["evidence"][0]["file_path"] == "src/utils/math.ts"


async def test_dismiss_finding_removes_it_from_open_filter(
    client: AsyncClient, index_repository_directly, analyze_repository_directly
):
    org_id, repo_id = await _indexed_and_analyzed_repository(
        client, index_repository_directly, analyze_repository_directly, "findings-dismiss@example.com"
    )

    listing = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/findings")
    finding_id = listing.json()[0]["id"]

    dismiss_response = await client.post(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/dismiss",
        json={"reason": "False positive — this is intentional test fixture data."},
    )
    assert dismiss_response.status_code == 200
    assert dismiss_response.json()["status"] == "dismissed"
    assert dismiss_response.json()["dismissed_reason"] is not None

    open_findings = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings",
        params={"status": "open"},
    )
    assert all(f["id"] != finding_id for f in open_findings.json())

    dismissed_findings = await client.get(
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings",
        params={"status": "dismissed"},
    )
    assert any(f["id"] == finding_id for f in dismissed_findings.json())
