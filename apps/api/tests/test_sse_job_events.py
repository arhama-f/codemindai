import asyncio
import json

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from codemind_api.db import SessionLocal, engine
from codemind_api.main import create_app
from codemind_api.routers.indexing import get_redis_pool
from codemind_shared_types.models import (
    GithubInstallation,
    JobRun,
    Organization,
    OrganizationMember,
    Repository,
    User,
)
class _FakeArqJob:
    job_id = "fake-arq-job-id"


class _FakeRedisPool:
    async def enqueue_job(self, *args, **kwargs) -> _FakeArqJob:
        return _FakeArqJob()


async def test_sse_stream_transitions_from_queued_to_completed():
    """Uses real (committing) sessions end-to-end, since the SSE endpoint
    polls via independent connections that can't see another connection's
    uncommitted transaction."""
    # Force fresh connections bound to this test's event loop — the engine is
    # a module-level singleton that other tests' loops may have already used.
    await engine.dispose()

    app = create_app()
    app.dependency_overrides[get_redis_pool] = lambda: _FakeRedisPool()
    transport = ASGITransport(app=app)

    created_org_id = None

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"email": "sse@example.com", "password": "hunter2", "full_name": "SSE Tester"},
            )
            org_response = await client.post("/api/organizations", json={"name": "SSE Org"})
            org_id = org_response.json()["id"]
            created_org_id = org_id

            await client.post(f"/api/organizations/{org_id}/github/connect")
            repo_response = await client.post(
                f"/api/organizations/{org_id}/repositories", json={"external_repo_id": "demo-1"}
            )
            repo_id = repo_response.json()["id"]

            index_response = await client.post(
                f"/api/organizations/{org_id}/repositories/{repo_id}/index"
            )
            job_id = index_response.json()["job_id"]

            async def advance_job_to_completed():
                await asyncio.sleep(0.6)
                async with SessionLocal() as session:
                    job_run = await session.get(JobRun, job_id)
                    job_run.status = "running"
                    job_run.progress_percent = 50
                    await session.commit()

                await asyncio.sleep(0.6)
                async with SessionLocal() as session:
                    job_run = await session.get(JobRun, job_id)
                    job_run.status = "completed"
                    job_run.progress_percent = 100
                    await session.commit()

            advancer = asyncio.create_task(advance_job_to_completed())

            observed_statuses = []
            async with client.stream(
                "GET", f"/api/organizations/{org_id}/jobs/{job_id}/events"
            ) as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = json.loads(line[len("data: ") :])
                    observed_statuses.append(payload["status"])
                    if payload["status"] == "completed":
                        break

            await advancer

        assert observed_statuses[0] == "queued"
        assert observed_statuses[-1] == "completed"
        assert "running" in observed_statuses
    finally:
        async with SessionLocal() as session:
            if created_org_id is not None:
                await session.execute(
                    delete(JobRun).where(JobRun.organization_id == created_org_id)
                )
                await session.execute(
                    delete(Repository).where(Repository.organization_id == created_org_id)
                )
                await session.execute(
                    delete(GithubInstallation).where(
                        GithubInstallation.organization_id == created_org_id
                    )
                )
                await session.execute(
                    delete(OrganizationMember).where(
                        OrganizationMember.organization_id == created_org_id
                    )
                )
                await session.execute(
                    delete(Organization).where(Organization.id == created_org_id)
                )
            await session.execute(delete(User).where(User.email == "sse@example.com"))
            await session.commit()
