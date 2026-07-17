from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from codemind_analysis_engine import CHECKS, analyze_file
from codemind_shared_types.models import (
    AnalysisRun,
    File,
    Finding,
    JobRun,
    Repository,
    RepositoryIndex,
    Symbol,
)
from codemind_shared_types.schemas import ParsedSymbol


def _utcnow() -> datetime:
    # DB timestamp columns are naive (TIMESTAMP WITHOUT TIME ZONE); strip tzinfo
    # after computing in UTC rather than using the deprecated datetime.utcnow().
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def analyze_repository(ctx: dict, *, repository_id: str, job_run_id: str) -> None:
    """Runs the deterministic bug/security/performance checks against the
    latest completed index of a repository, storing results as `Finding` rows
    under a new `AnalysisRun`. Needs only a DB session — no GitHub/AI/embedding
    provider, since it reads already-persisted files/symbols."""
    sessionmaker = ctx["db_sessionmaker"]

    async with sessionmaker() as session:
        job_run = await session.get(JobRun, UUID(job_run_id))
        repository = await session.get(Repository, UUID(repository_id))

        job_run.status = "running"
        job_run.started_at = _utcnow()
        job_run.progress_percent = 0
        await session.commit()

        analysis_run: AnalysisRun | None = None
        try:
            index_result = await session.execute(
                select(RepositoryIndex)
                .where(
                    RepositoryIndex.repository_id == repository.id,
                    RepositoryIndex.status == "completed",
                )
                .order_by(RepositoryIndex.created_at.desc())
                .limit(1)
            )
            repository_index = index_result.scalar_one_or_none()
            if repository_index is None:
                raise ValueError("Repository must be indexed before it can be analyzed.")

            analysis_run = AnalysisRun(
                organization_id=repository.organization_id,
                repository_id=repository.id,
                repository_index_id=repository_index.id,
                status="running",
                started_at=_utcnow(),
            )
            session.add(analysis_run)
            await session.flush()
            job_run.progress_percent = 10
            await session.commit()

            files_result = await session.execute(
                select(File).where(File.repository_index_id == repository_index.id)
            )
            files = files_result.scalars().all()

            symbols_result = await session.execute(
                select(Symbol).where(Symbol.file_id.in_([f.id for f in files]))
            )
            symbols_by_file: dict[UUID, list[Symbol]] = {}
            for symbol in symbols_result.scalars().all():
                symbols_by_file.setdefault(symbol.file_id, []).append(symbol)
            job_run.progress_percent = 30
            await session.commit()

            by_severity: dict[str, int] = {}
            by_category: dict[str, int] = {}
            total = 0

            for file_row in files:
                file_symbols = symbols_by_file.get(file_row.id, [])
                parsed_symbols = [
                    ParsedSymbol(
                        name=s.name,
                        kind=s.kind,
                        start_line=s.start_line,
                        end_line=s.end_line,
                        signature=s.signature,
                        exported=s.exported,
                    )
                    for s in file_symbols
                ]
                drafts = analyze_file(file_row.path, file_row.content, parsed_symbols)

                for draft in drafts:
                    symbol_id = next(
                        (
                            s.id
                            for s in file_symbols
                            if s.start_line <= draft.start_line <= s.end_line
                        ),
                        None,
                    )
                    session.add(
                        Finding(
                            organization_id=repository.organization_id,
                            analysis_run_id=analysis_run.id,
                            repository_index_id=repository_index.id,
                            file_id=file_row.id,
                            symbol_id=symbol_id,
                            check_id=draft.check_id,
                            category=draft.category,
                            title=draft.title,
                            severity=draft.severity,
                            confidence=draft.confidence,
                            explanation=draft.explanation,
                            recommended_fix=draft.recommended_fix,
                            suggested_test=draft.suggested_test,
                            execution_path=draft.execution_path,
                            start_line=draft.start_line,
                            end_line=draft.end_line,
                            evidence=[e.model_dump() for e in draft.evidence],
                        )
                    )
                    total += 1
                    by_severity[draft.severity] = by_severity.get(draft.severity, 0) + 1
                    by_category[draft.category] = by_category.get(draft.category, 0) + 1

            job_run.progress_percent = 90
            await session.commit()

            analysis_run.status = "completed"
            analysis_run.completed_at = _utcnow()
            analysis_run.stats = {
                "total": total,
                "by_severity": by_severity,
                "by_category": by_category,
                "checks_run": [check.__name__ for check in CHECKS],
            }
            job_run.status = "completed"
            job_run.progress_percent = 100
            job_run.message = "analysis completed"
            job_run.completed_at = _utcnow()
            await session.commit()

        except Exception as exc:
            await session.rollback()
            job_run.status = "failed"
            job_run.error_message = str(exc)
            job_run.completed_at = _utcnow()
            if analysis_run is not None:
                analysis_run.status = "failed"
                analysis_run.error_message = str(exc)
            await session.commit()
            raise
