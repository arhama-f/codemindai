from abc import ABC, abstractmethod

from codemind_shared_types.schemas import (
    PullRequestDetailDTO,
    PullRequestDTO,
    PullRequestFileDTO,
    RemoteFileDTO,
    ReviewCommentDTO,
    ReviewResultDTO,
)


class GitHubWriteClient(ABC):
    """Write-side GitHub operations: reading a file's current state, creating
    branches, updating file content, and opening pull requests. Deliberately
    separate from the read-only `GitHubClient` interface (used for indexing) —
    this one is only exercised by the propose-fix/publish workflow."""

    @abstractmethod
    async def get_file(self, *, owner: str, repo: str, path: str, branch: str) -> RemoteFileDTO: ...

    @abstractmethod
    async def create_branch(
        self, *, owner: str, repo: str, base_branch: str, new_branch: str
    ) -> None: ...

    @abstractmethod
    async def update_file(
        self,
        *,
        owner: str,
        repo: str,
        path: str,
        branch: str,
        content: str,
        sha: str | None,
        message: str,
    ) -> None:
        """Create or update a file. Pass the sha from `get_file` to update an
        existing file (rejected if the file has changed since); pass `None`
        to create a new file at `path`."""
        ...

    @abstractmethod
    async def create_pull_request(
        self,
        *,
        owner: str,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = True,
    ) -> PullRequestDTO: ...

    @abstractmethod
    async def get_pull_request(
        self, *, owner: str, repo: str, pr_number: int
    ) -> PullRequestDetailDTO: ...

    @abstractmethod
    async def get_pull_request_files(
        self, *, owner: str, repo: str, pr_number: int
    ) -> list[PullRequestFileDTO]: ...

    @abstractmethod
    async def create_review(
        self,
        *,
        owner: str,
        repo: str,
        pr_number: int,
        commit_sha: str,
        body: str,
        comments: list[ReviewCommentDTO],
    ) -> ReviewResultDTO: ...

    @abstractmethod
    async def create_commit_status(
        self,
        *,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str,
        context: str,
    ) -> None: ...
