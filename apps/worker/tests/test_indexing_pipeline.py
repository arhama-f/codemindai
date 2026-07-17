from sqlalchemy import select

from codemind_shared_types.models import (
    CodeChunk,
    Embedding,
    File,
    GithubInstallation,
    JobRun,
    Organization,
    Repository,
    RepositoryIndex,
    RepositorySummary,
    Symbol,
    SymbolRelationship,
)
from codemind_worker.tasks.index_repository import index_repository


async def _seed_repository(db_session):
    organization = Organization(name="Pipeline Test Org", slug="pipeline-test-org")
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

    job_run = JobRun(organization_id=organization.id, repository_id=repository.id)
    db_session.add(job_run)
    await db_session.commit()

    return organization, repository, job_run


async def test_index_repository_completes_and_populates_everything(db_session, worker_ctx):
    organization, repository, job_run = await _seed_repository(db_session)

    await index_repository(
        worker_ctx, repository_id=str(repository.id), job_run_id=str(job_run.id)
    )

    await db_session.refresh(job_run)
    assert job_run.status == "completed"
    assert job_run.progress_percent == 100

    index_result = await db_session.execute(
        select(RepositoryIndex).where(RepositoryIndex.repository_id == repository.id)
    )
    repository_index = index_result.scalar_one()
    assert repository_index.status == "completed"
    assert repository_index.stats["file_count"] == 6

    files_result = await db_session.execute(
        select(File).where(File.repository_index_id == repository_index.id)
    )
    files_by_path = {f.path: f for f in files_result.scalars().all()}
    assert set(files_by_path.keys()) == {
        "src/index.ts",
        "src/utils/math.ts",
        "src/utils/string.ts",
        "src/models/user.ts",
        "src/services/userService.ts",
        "src/components/UserCard.tsx",
    }

    symbols_result = await db_session.execute(
        select(Symbol).where(Symbol.file_id == files_by_path["src/utils/math.ts"].id)
    )
    math_symbols = {s.name: s for s in symbols_result.scalars().all()}
    assert set(math_symbols.keys()) == {"add", "subtract", "multiply", "divide"}
    assert math_symbols["divide"].start_line == 14
    assert math_symbols["divide"].end_line == 16

    relationships_result = await db_session.execute(
        select(SymbolRelationship).where(
            SymbolRelationship.from_file_id == files_by_path["src/index.ts"].id
        )
    )
    relationships = relationships_result.scalars().all()
    resolved_targets = {r.to_file_id for r in relationships if r.to_file_id is not None}
    assert files_by_path["src/utils/math.ts"].id in resolved_targets

    chunks_result = await db_session.execute(
        select(CodeChunk).where(CodeChunk.repository_index_id == repository_index.id)
    )
    chunks = chunks_result.scalars().all()
    assert len(chunks) > 0
    assert all(c.content.strip() for c in chunks)

    embeddings_result = await db_session.execute(
        select(Embedding).where(Embedding.code_chunk_id.in_([c.id for c in chunks]))
    )
    embeddings = embeddings_result.scalars().all()
    assert len(embeddings) == len(chunks)
    assert all(e.vector is not None and len(e.vector) == 384 for e in embeddings)
    assert repository_index.stats["embedding_count"] == len(chunks)

    summaries_result = await db_session.execute(
        select(RepositorySummary).where(
            RepositorySummary.repository_index_id == repository_index.id
        )
    )
    summaries = summaries_result.scalars().all()
    repo_scope_summaries = [s for s in summaries if s.scope == "repository"]
    directory_scope_summaries = [s for s in summaries if s.scope == "directory"]
    assert len(repo_scope_summaries) == 1
    assert len(directory_scope_summaries) >= 1
    assert all(s.summary.strip() for s in summaries)


async def test_index_repository_marks_failed_on_error(db_session, worker_ctx):
    organization, repository, job_run = await _seed_repository(db_session)

    broken_ctx = {**worker_ctx, "github_client": None}

    raised = False
    try:
        await index_repository(
            broken_ctx, repository_id=str(repository.id), job_run_id=str(job_run.id)
        )
    except AttributeError:
        raised = True

    assert raised

    await db_session.refresh(job_run)
    assert job_run.status == "failed"
    assert job_run.error_message is not None
