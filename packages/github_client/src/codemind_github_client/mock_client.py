import hashlib
from datetime import datetime
from pathlib import Path

from codemind_github_client.interface import GitHubClient
from codemind_shared_types.schemas import (
    BranchDTO,
    CommitDTO,
    FileContentDTO,
    InstallationDTO,
    RepositoryDTO,
    RepositorySnapshot,
)

MOCK_INSTALLATION_ID = "mock-install-1"
MOCK_ACCOUNT_LOGIN = "codemind-demo"
MOCK_REPO_EXTERNAL_ID = "demo-1"
MOCK_REPO_FULL_NAME = "codemind-demo/todo-app-ts"
MOCK_REPO_DEFAULT_BRANCH = "main"

# Fixed (not `now()`) so the snapshot is deterministic across test runs.
MOCK_COMMIT_SHA = hashlib.sha256(b"demo-repo-v1").hexdigest()[:40]
MOCK_COMMIT_TIMESTAMP = datetime(2024, 1, 1)

PARSEABLE_EXTENSIONS = (".ts", ".tsx")


class MockGitHubClient(GitHubClient):
    """Serves one hardcoded installation + demo repo, reading files from the
    bundled fixture repo on disk instead of calling the real GitHub API."""

    def __init__(self, demo_repo_root: str | Path):
        self._demo_repo_root = Path(demo_repo_root)

    async def list_installations(self, *, user_id: str) -> list[InstallationDTO]:
        return [
            InstallationDTO(
                external_installation_id=MOCK_INSTALLATION_ID, account_login=MOCK_ACCOUNT_LOGIN
            )
        ]

    async def list_repositories(self, *, installation_id: str) -> list[RepositoryDTO]:
        return [
            RepositoryDTO(
                external_repo_id=MOCK_REPO_EXTERNAL_ID,
                full_name=MOCK_REPO_FULL_NAME,
                default_branch=MOCK_REPO_DEFAULT_BRANCH,
            )
        ]

    async def get_repository_snapshot(
        self, *, installation_id: str, external_repo_id: str
    ) -> RepositorySnapshot:
        src_root = self._demo_repo_root / "src"
        files: list[FileContentDTO] = []
        for path in sorted(src_root.rglob("*")):
            if path.is_file() and path.suffix in PARSEABLE_EXTENSIONS:
                relative_path = f"src/{path.relative_to(src_root).as_posix()}"
                files.append(FileContentDTO(path=relative_path, content=path.read_text()))

        return RepositorySnapshot(
            branch=BranchDTO(name=MOCK_REPO_DEFAULT_BRANCH, is_default=True),
            commit=CommitDTO(
                sha=MOCK_COMMIT_SHA,
                message="Initial demo repository snapshot",
                author_name="CodeMind Demo",
                author_email="demo@codemind.ai",
                committed_at=MOCK_COMMIT_TIMESTAMP,
            ),
            files=files,
        )
