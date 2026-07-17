from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID

from codemind_ai_orchestrator import AIProvider
from codemind_code_parser import chunk_file, parse_file, resolve_import_path
from codemind_embedding_provider import EmbeddingProvider
from codemind_github_client import GitHubClient
from codemind_shared_types.models import (
    Branch,
    CodeChunk,
    Commit,
    Embedding,
    File,
    GithubInstallation,
    JobRun,
    Repository,
    RepositoryIndex,
    RepositorySummary,
    Symbol,
    SymbolRelationship,
)
from codemind_shared_types.schemas import FileSummaryDTO

PARSEABLE_EXTENSIONS = (".ts", ".tsx")


def _utcnow() -> datetime:
    # DB timestamp columns are naive (TIMESTAMP WITHOUT TIME ZONE); strip tzinfo
    # after computing in UTC rather than using the deprecated datetime.utcnow().
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def index_repository(ctx: dict, *, repository_id: str, job_run_id: str) -> None:
    """Fetches a repository snapshot, parses its TS/TSX files, and stores
    files/symbols/relationships/chunks/summaries. `ctx` carries a DB session
    factory plus GitHubClient/AIProvider instances, so this same function
    works identically whether invoked directly (as in tests) or via the real
    arq worker."""
    sessionmaker = ctx["db_sessionmaker"]
    github_client: GitHubClient = ctx["github_client"]
    ai_provider: AIProvider = ctx["ai_provider"]
    embedding_provider: EmbeddingProvider = ctx["embedding_provider"]

    async with sessionmaker() as session:
        job_run = await session.get(JobRun, UUID(job_run_id))
        repository = await session.get(Repository, UUID(repository_id))
        installation = await session.get(GithubInstallation, repository.installation_id)

        job_run.status = "running"
        job_run.started_at = _utcnow()
        job_run.progress_percent = 0
        await session.commit()

        repository_index: RepositoryIndex | None = None
        try:
            snapshot = await github_client.get_repository_snapshot(
                installation_id=installation.external_installation_id,
                external_repo_id=repository.external_repo_id,
            )
            job_run.progress_percent = 10
            job_run.message = "fetched snapshot"
            await session.commit()

            branch = Branch(
                repository_id=repository.id,
                name=snapshot.branch.name,
                is_default=snapshot.branch.is_default,
            )
            session.add(branch)
            await session.flush()

            commit = Commit(
                repository_id=repository.id,
                branch_id=branch.id,
                sha=snapshot.commit.sha,
                message=snapshot.commit.message,
                author_name=snapshot.commit.author_name,
                author_email=snapshot.commit.author_email,
                committed_at=snapshot.commit.committed_at,
            )
            session.add(commit)
            await session.flush()

            repository_index = RepositoryIndex(
                organization_id=repository.organization_id,
                repository_id=repository.id,
                commit_id=commit.id,
                status="running",
                started_at=_utcnow(),
            )
            session.add(repository_index)
            await session.flush()

            parseable_files = [f for f in snapshot.files if f.path.endswith(PARSEABLE_EXTENSIONS)]
            parsed_by_path = {
                f.path: parse_file(f.path, f.content) for f in parseable_files
            }

            file_rows: dict[str, File] = {}
            for file_content in parseable_files:
                language = "tsx" if file_content.path.endswith(".tsx") else "typescript"
                file_row = File(
                    organization_id=repository.organization_id,
                    repository_index_id=repository_index.id,
                    path=file_content.path,
                    language=language,
                    size_bytes=len(file_content.content.encode("utf-8")),
                    content_hash=sha256(file_content.content.encode("utf-8")).hexdigest(),
                    content=file_content.content,
                )
                session.add(file_row)
                file_rows[file_content.path] = file_row
            await session.flush()
            job_run.progress_percent = 40
            await session.commit()

            symbols_by_path: dict[str, list[Symbol]] = {}
            for path, parsed in parsed_by_path.items():
                file_row = file_rows[path]
                symbol_rows = [
                    Symbol(
                        organization_id=repository.organization_id,
                        file_id=file_row.id,
                        name=parsed_symbol.name,
                        kind=parsed_symbol.kind,
                        start_line=parsed_symbol.start_line,
                        end_line=parsed_symbol.end_line,
                        signature=parsed_symbol.signature,
                        exported=parsed_symbol.exported,
                    )
                    for parsed_symbol in parsed.symbols
                ]
                session.add_all(symbol_rows)
                symbols_by_path[path] = symbol_rows
            await session.flush()
            job_run.progress_percent = 55
            await session.commit()

            known_paths = set(file_rows.keys())
            for path, parsed in parsed_by_path.items():
                from_file = file_rows[path]
                for parsed_import in parsed.imports:
                    resolved_path = resolve_import_path(path, parsed_import.specifier, known_paths)
                    to_file = file_rows.get(resolved_path) if resolved_path else None
                    to_symbols_by_name = {
                        s.name: s for s in symbols_by_path.get(resolved_path, []) if s.exported
                    }

                    # One relationship row per imported name so impact analysis can
                    # find dependents of a specific symbol, not just of a file. A
                    # side-effect-only import (no named imports) gets one row with
                    # no symbol resolved.
                    imported_names = parsed_import.imported_names or [None]
                    for imported_name in imported_names:
                        to_symbol = (
                            to_symbols_by_name.get(imported_name) if imported_name else None
                        )
                        if to_symbol is not None:
                            confidence = "confirmed_static"
                        elif to_file is not None:
                            confidence = "unknown"
                        else:
                            confidence = None

                        session.add(
                            SymbolRelationship(
                                organization_id=repository.organization_id,
                                repository_index_id=repository_index.id,
                                from_file_id=from_file.id,
                                to_file_id=to_file.id if to_file else None,
                                to_symbol_id=to_symbol.id if to_symbol else None,
                                relationship_type="imports",
                                raw_specifier=parsed_import.specifier,
                                confidence=confidence,
                            )
                        )
            job_run.progress_percent = 65
            await session.commit()

            all_chunk_rows: list[CodeChunk] = []
            for file_content in parseable_files:
                path = file_content.path
                file_row = file_rows[path]
                chunks = chunk_file(file_content.content, parsed_by_path[path].symbols)
                chunk_rows = [
                    CodeChunk(
                        organization_id=repository.organization_id,
                        file_id=file_row.id,
                        repository_index_id=repository_index.id,
                        chunk_index=chunk.chunk_index,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        content=chunk.content,
                    )
                    for chunk in chunks
                ]
                session.add_all(chunk_rows)
                all_chunk_rows.extend(chunk_rows)
            await session.flush()  # populate chunk.id for the embeddings step below
            job_run.progress_percent = 80
            await session.commit()

            vectors = await embedding_provider.embed([c.content for c in all_chunk_rows])
            session.add_all(
                Embedding(
                    code_chunk_id=chunk_row.id,
                    model_name=embedding_provider.model_name,
                    vector=vector,
                )
                for chunk_row, vector in zip(all_chunk_rows, vectors)
            )
            job_run.progress_percent = 88
            await session.commit()

            file_summaries: list[FileSummaryDTO] = []
            for file_content in parseable_files:
                parsed = parsed_by_path[file_content.path]
                summary_text = await ai_provider.summarize_file(
                    file_path=file_content.path, content=file_content.content, symbols=parsed.symbols
                )
                file_summaries.append(
                    FileSummaryDTO(
                        file_path=file_content.path, summary=summary_text, symbols=parsed.symbols
                    )
                )

            by_directory: dict[str, list[FileSummaryDTO]] = {}
            for file_summary in file_summaries:
                directory = "/".join(file_summary.file_path.split("/")[:-1]) or "."
                by_directory.setdefault(directory, []).append(file_summary)

            for directory, summaries in sorted(by_directory.items()):
                summary_text = await ai_provider.summarize_directory(
                    dir_path=directory, file_summaries=summaries
                )
                session.add(
                    RepositorySummary(
                        organization_id=repository.organization_id,
                        repository_index_id=repository_index.id,
                        scope="directory",
                        path=directory,
                        summary=summary_text,
                    )
                )

            repo_summary_text = await ai_provider.summarize_directory(
                dir_path=".", file_summaries=file_summaries
            )
            session.add(
                RepositorySummary(
                    organization_id=repository.organization_id,
                    repository_index_id=repository_index.id,
                    scope="repository",
                    path=None,
                    summary=repo_summary_text,
                )
            )
            job_run.progress_percent = 95
            await session.commit()

            repository_index.status = "completed"
            repository_index.completed_at = _utcnow()
            repository_index.stats = {
                "file_count": len(file_rows),
                "symbol_count": sum(len(v) for v in symbols_by_path.values()),
                "relationship_count": sum(
                    len(parsed_import.imported_names) or 1
                    for p in parsed_by_path.values()
                    for parsed_import in p.imports
                ),
                "embedding_count": len(all_chunk_rows),
            }
            job_run.status = "completed"
            job_run.progress_percent = 100
            job_run.message = "index completed"
            job_run.completed_at = _utcnow()
            await session.commit()

        except Exception as exc:
            await session.rollback()
            job_run.status = "failed"
            job_run.error_message = str(exc)
            job_run.completed_at = _utcnow()
            if repository_index is not None:
                repository_index.status = "failed"
                repository_index.error_message = str(exc)
            await session.commit()
            raise
