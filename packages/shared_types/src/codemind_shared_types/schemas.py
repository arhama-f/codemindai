from datetime import datetime

from pydantic import BaseModel

# --- GitHub client DTOs ---


class InstallationDTO(BaseModel):
    external_installation_id: str
    account_login: str


class RepositoryDTO(BaseModel):
    external_repo_id: str
    full_name: str
    default_branch: str


class BranchDTO(BaseModel):
    name: str
    is_default: bool


class CommitDTO(BaseModel):
    sha: str
    message: str
    author_name: str
    author_email: str
    committed_at: datetime


class FileContentDTO(BaseModel):
    path: str
    content: str


class RepositorySnapshot(BaseModel):
    branch: BranchDTO
    commit: CommitDTO
    files: list[FileContentDTO]


# --- Code parser DTOs ---


class ParsedSymbol(BaseModel):
    name: str
    kind: str
    start_line: int
    end_line: int
    signature: str | None = None
    exported: bool = False


class ParsedImport(BaseModel):
    specifier: str
    imported_names: list[str] = []


class ParsedFile(BaseModel):
    symbols: list[ParsedSymbol]
    imports: list[ParsedImport]


class Chunk(BaseModel):
    chunk_index: int
    start_line: int
    end_line: int
    content: str


# --- AI orchestrator DTOs ---


class FileSummaryDTO(BaseModel):
    file_path: str
    summary: str
    symbols: list[ParsedSymbol] = []


class SubsystemDTO(BaseModel):
    name: str
    file_paths: list[str]


class RetrievedChunkDTO(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


# --- Analysis engine DTOs ---


class FindingEvidenceDTO(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class FindingDraftDTO(BaseModel):
    check_id: str
    category: str
    title: str
    severity: str
    confidence: str
    explanation: str
    recommended_fix: str
    suggested_test: str | None = None
    execution_path: str | None = None
    file_path: str
    start_line: int
    end_line: int
    evidence: list[FindingEvidenceDTO]
