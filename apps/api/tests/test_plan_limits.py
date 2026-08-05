from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api import plan_limits
from codemind_shared_types.models import GithubInstallation, Repository, Subscription


async def _org_with_github_connected(client: AsyncClient, email: str, org_name: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": org_name})
    org_id = created.json()["id"]
    await client.post(f"/api/organizations/{org_id}/github/connect")
    return org_id




async def test_new_org_gets_a_free_subscription(client: AsyncClient):
    org_id = await _org_with_github_connected(client, "billing-new@example.com", "New Org")

    response = await client.get(f"/api/organizations/{org_id}/billing")
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body["status"] == "active"
    assert body["usage"]["repositories"] == {"used": 0, "limit": 1}
    assert body["usage"]["ai_actions_per_month"] == {"used": 0, "limit": 20}


async def test_free_plan_blocks_a_second_repository(client: AsyncClient):
    org_id = await _org_with_github_connected(client, "limit-repo@example.com", "Limit Repo Org")

    first = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    assert first.status_code == 201

    # Free plan's repository limit is 1 — a second add (even a duplicate of
    # the same repo) should be blocked before the handler's own
    # already-exists check runs.
    second = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    assert second.status_code == 402


async def test_free_plan_blocks_ai_actions_past_the_monthly_limit(
    client: AsyncClient, index_repository_directly, analyze_repository_directly, monkeypatch
):
    # Shrink the free plan's monthly AI-action limit for this test only, so
    # we don't need 20+ real calls to exercise the 402 path.
    monkeypatch.setitem(plan_limits.PLAN_LIMITS["free"], "ai_actions_per_month", 2)

    org_id = await _org_with_github_connected(client, "limit-ai@example.com", "Limit AI Org")
    repo = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    repo_id = repo.json()["id"]

    index_job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/index")
    await index_repository_directly(repository_id=repo_id, job_run_id=index_job.json()["job_id"])
    analyze_job = await client.post(f"/api/organizations/{org_id}/repositories/{repo_id}/analyses")
    await analyze_repository_directly(
        repository_id=repo_id, job_run_id=analyze_job.json()["job_id"]
    )

    findings = await client.get(f"/api/organizations/{org_id}/repositories/{repo_id}/findings")
    finding_id = findings.json()[0]["id"]

    explain_url = (
        f"/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/explain"
    )
    first = await client.post(explain_url)
    assert first.status_code == 201
    second = await client.post(explain_url)
    assert second.status_code == 201
    third = await client.post(explain_url)
    assert third.status_code == 402


async def test_team_plan_has_no_repository_limit(client: AsyncClient, db_session: AsyncSession):
    org_id = await _org_with_github_connected(client, "limit-team@example.com", "Team Org")
    installation_result = await db_session.execute(
        select(GithubInstallation).where(GithubInstallation.organization_id == org_id)
    )
    installation_id = installation_result.scalar_one().id

    # Seed repositories directly rather than through the API — the mock
    # GitHub client only ever exposes one demo repo, so this is the only way
    # to simulate an org already over the free plan's limit.
    for i in range(3):
        db_session.add(
            Repository(
                organization_id=org_id,
                installation_id=installation_id,
                external_repo_id=f"seeded-{i}",
                full_name=f"seeded/repo-{i}",
                default_branch="main",
            )
        )
    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    subscription = result.scalar_one()
    subscription.plan = "team"
    await db_session.commit()

    response = await client.post(
        f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
    )
    assert response.status_code == 201
