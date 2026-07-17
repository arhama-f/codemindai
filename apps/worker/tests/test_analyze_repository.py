import pytest
from sqlalchemy import select

from codemind_shared_types.models import (
    AnalysisRun,
    Finding,
    GithubInstallation,
    JobRun,
    Organization,
    Repository,
)
from codemind_worker.tasks.analyze_repository import analyze_repository
from codemind_worker.tasks.index_repository import index_repository


async def _seed_and_index_repository(db_session, worker_ctx):
    organization = Organization(name="Analyze Test Org", slug="analyze-test-org")
    db_session.add(organization)
    await db_session.flush()

    installation = GithubInstallation(
        organization_id=organization.id,
        provider="mock",
        external_installation_id="mock-install-1",
        account_login="codemind-demo",
    )
    db_session.add(installation)
    await db_session.flush()

    repository = Repository(
        organization_id=organization.id,
        installation_id=installation.id,
        external_repo_id="demo-1",
        full_name="codemind-demo/todo-app-ts",
        default_branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    index_job_run = JobRun(organization_id=organization.id, repository_id=repository.id)
    db_session.add(index_job_run)
    await db_session.commit()

    await index_repository(
        worker_ctx, repository_id=str(repository.id), job_run_id=str(index_job_run.id)
    )

    return organization, repository


async def test_analyze_repository_finds_all_nine_planted_issues(db_session, worker_ctx):
    organization, repository = await _seed_and_index_repository(db_session, worker_ctx)

    analyze_job_run = JobRun(
        organization_id=organization.id, repository_id=repository.id, job_type="analyze_repository"
    )
    db_session.add(analyze_job_run)
    await db_session.commit()

    await analyze_repository(
        worker_ctx, repository_id=str(repository.id), job_run_id=str(analyze_job_run.id)
    )

    await db_session.refresh(analyze_job_run)
    assert analyze_job_run.status == "completed"
    assert analyze_job_run.progress_percent == 100

    analysis_run_result = await db_session.execute(
        select(AnalysisRun).where(AnalysisRun.repository_id == repository.id)
    )
    analysis_run = analysis_run_result.scalar_one()
    assert analysis_run.status == "completed"
    assert analysis_run.stats["total"] == 9
    assert analysis_run.stats["by_category"] == {"bug": 3, "security": 3, "performance": 3}

    findings_result = await db_session.execute(
        select(Finding).where(Finding.analysis_run_id == analysis_run.id)
    )
    findings = findings_result.scalars().all()
    check_ids = {f.check_id for f in findings}
    assert check_ids == {
        "unsafe-division",
        "empty-catch-block",
        "unreachable-code-after-return",
        "hardcoded-secret",
        "unsafe-dangerously-set-inner-html",
        "sensitive-data-logging",
        "nested-loop-quadratic",
        "array-scan-in-loop",
        "array-rebuild-in-loop",
    }
    assert all(f.status == "open" for f in findings)

    # config.ts's findings have no resolvable symbol_id — `const` declarations
    # aren't extracted as top-level symbols by the parser — but findings
    # inside an actual function/method/class should resolve one.
    division_finding = next(f for f in findings if f.check_id == "unsafe-division")
    assert division_finding.symbol_id is not None


async def test_analyze_repository_fails_when_not_yet_indexed(db_session, worker_ctx):
    organization = Organization(name="Not Indexed Org", slug="not-indexed-analyze-org")
    db_session.add(organization)
    await db_session.flush()

    installation = GithubInstallation(
        organization_id=organization.id,
        provider="mock",
        external_installation_id="mock-install-1",
        account_login="codemind-demo",
    )
    db_session.add(installation)
    await db_session.flush()

    repository = Repository(
        organization_id=organization.id,
        installation_id=installation.id,
        external_repo_id="demo-1",
        full_name="codemind-demo/todo-app-ts",
        default_branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    job_run = JobRun(
        organization_id=organization.id, repository_id=repository.id, job_type="analyze_repository"
    )
    db_session.add(job_run)
    await db_session.commit()

    with pytest.raises(ValueError, match="must be indexed"):
        await analyze_repository(
            worker_ctx, repository_id=str(repository.id), job_run_id=str(job_run.id)
        )

    await db_session.refresh(job_run)
    assert job_run.status == "failed"
    assert job_run.error_message is not None
