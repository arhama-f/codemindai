import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from codemind_shared_types.db import Base


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class User(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=text("now()")
    )


class Organization(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class OrganizationMember(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String, CheckConstraint("role in ('owner','member')"), nullable=False
    )


class GithubInstallation(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "github_installations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String, server_default="mock")
    external_installation_id: Mapped[str] = mapped_column(String, nullable=False)
    account_login: Mapped[str] = mapped_column(String, nullable=False)


class Repository(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("organization_id", "external_repo_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    installation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("github_installations.id"), nullable=False
    )
    external_repo_id: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    default_branch: Mapped[str] = mapped_column(String, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, server_default="false")


class Branch(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "branches"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, server_default="false")


class Commit(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "commits"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    sha: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str] = mapped_column(String, nullable=False)
    author_email: Mapped[str] = mapped_column(String, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(nullable=False)


class RepositoryIndex(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "repository_indexes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commits.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String,
        CheckConstraint("status in ('pending','running','completed','failed')"),
        server_default="pending",
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class File(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "files"
    __table_args__ = (UniqueConstraint("repository_index_id", "path"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class Symbol(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "symbols"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    exported: Mapped[bool] = mapped_column(Boolean, server_default="false")


class SymbolRelationship(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "symbol_relationships"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    from_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )
    to_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=True
    )
    from_symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=True
    )
    to_symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=True
    )
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)
    raw_specifier: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)


class CodeChunk(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "code_chunks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Embedding(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "embeddings"
    __table_args__ = (UniqueConstraint("code_chunk_id", "model_name"),)

    code_chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("code_chunks.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)


class RepositorySummary(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "repository_summaries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    scope: Mapped[str] = mapped_column(
        String, CheckConstraint("scope in ('repository','directory')"), nullable=False
    )
    path: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String, server_default="mock")


class JobRun(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "job_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=True
    )
    job_type: Mapped[str] = mapped_column(String, server_default="index_repository")
    arq_job_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        CheckConstraint("status in ('queued','running','completed','failed')"),
        server_default="queued",
    )
    progress_percent: Mapped[int] = mapped_column(Integer, server_default="0")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class AnalysisRun(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "analysis_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String,
        CheckConstraint("status in ('pending','running','completed','failed')"),
        server_default="pending",
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Finding(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "findings"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id"), nullable=False
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repository_indexes.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )
    symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=True
    )

    check_id: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(
        String, CheckConstraint("category in ('bug','security','performance')"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(
        String, CheckConstraint("severity in ('critical','high','medium','low')"), nullable=False
    )
    confidence: Mapped[str] = mapped_column(
        String, CheckConstraint("confidence in ('high','medium','low')"), nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_fix: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_test: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False)

    status: Mapped[str] = mapped_column(
        String, CheckConstraint("status in ('open','dismissed')"), server_default="open"
    )
    dismissed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    dismissed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class ProposedChange(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "proposed_changes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    updated_content: Mapped[str] = mapped_column(Text, nullable=False)
    test_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_file_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_by: Mapped[str] = mapped_column(
        String, CheckConstraint("generated_by in ('mock','claude')"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, CheckConstraint("status in ('draft','published')"), server_default="draft"
    )
    pr_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class FindingExplanation(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "finding_explanations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False
    )

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(
        String, CheckConstraint("generated_by in ('mock','claude')"), nullable=False
    )


class PRReview(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "pr_reviews"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    owner: Mapped[str] = mapped_column(String, nullable=False)
    repo: Mapped[str] = mapped_column(String, nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_sha: Mapped[str] = mapped_column(String, nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comments_posted: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String, CheckConstraint("status in ('success','failure')"), nullable=False
    )
    review_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
