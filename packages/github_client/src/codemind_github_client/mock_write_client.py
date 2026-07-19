import hashlib

from codemind_github_client.write_interface import GitHubWriteClient
from codemind_shared_types.schemas import (
    PullRequestDetailDTO,
    PullRequestDTO,
    PullRequestFileDTO,
    RemoteFileDTO,
    ReviewCommentDTO,
    ReviewResultDTO,
)


def _compute_sha(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:40]


class MockGitHubWriteClient(GitHubWriteClient):
    """In-memory GitHub write client for tests. Seed it with the file content a
    real repo would have; `update_file` bumps the sha like a real commit would,
    so staleness checks against a stale sha behave the same as the real API."""

    def __init__(self, seed_files: dict[tuple[str, str, str], str] | None = None):
        self._files: dict[tuple[str, str, str], dict[str, str]] = {}
        for key, content in (seed_files or {}).items():
            self._files[key] = {"content": content, "sha": _compute_sha(content)}
        self.created_branches: list[dict[str, str]] = []
        self.created_pull_requests: list[PullRequestDTO] = []
        self.created_reviews: list[dict] = []
        self.created_commit_statuses: list[dict] = []
        self._pr_counter = 0
        self._pull_requests: dict[tuple[str, str, int], PullRequestDetailDTO] = {}
        self._pull_request_files: dict[tuple[str, str, int], list[PullRequestFileDTO]] = {}
        self._review_counter = 0

    def seed_pull_request(
        self,
        *,
        owner: str,
        repo: str,
        pr_number: int,
        title: str = "Test PR",
        head_sha: str,
        head_ref: str,
        base_ref: str,
        files: list[PullRequestFileDTO],
    ) -> None:
        """Register a fake open PR (and its changed files) for the PR-review
        flow to fetch, mirroring `seed()`'s role for the propose-fix flow."""
        key = (owner, repo, pr_number)
        self._pull_requests[key] = PullRequestDetailDTO(
            number=pr_number, title=title, head_sha=head_sha, head_ref=head_ref, base_ref=base_ref
        )
        self._pull_request_files[key] = files

    def seed(self, *, owner: str, repo: str, path: str, content: str) -> None:
        """Set or overwrite a file's content after construction — useful in
        tests that don't know the content until later (e.g. it comes from an
        already-indexed repository)."""
        self._files[(owner, repo, path)] = {"content": content, "sha": _compute_sha(content)}

    async def get_file(self, *, owner: str, repo: str, path: str, branch: str) -> RemoteFileDTO:
        entry = self._files.get((owner, repo, path))
        if entry is None:
            raise FileNotFoundError(f"{owner}/{repo}:{path}@{branch} not found in mock write client")
        return RemoteFileDTO(path=path, sha=entry["sha"], content=entry["content"])

    async def create_branch(
        self, *, owner: str, repo: str, base_branch: str, new_branch: str
    ) -> None:
        self.created_branches.append(
            {"owner": owner, "repo": repo, "base_branch": base_branch, "new_branch": new_branch}
        )

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
        key = (owner, repo, path)
        entry = self._files.get(key)
        if sha is None:
            if entry is not None:
                raise ValueError(f"{owner}/{repo}:{path} already exists — sha is required to update it")
        elif entry is None or entry["sha"] != sha:
            raise ValueError(f"stale or unknown sha for {owner}/{repo}:{path}")
        self._files[key] = {"content": content, "sha": _compute_sha(content)}

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
    ) -> PullRequestDTO:
        self._pr_counter += 1
        pull_request = PullRequestDTO(
            number=self._pr_counter,
            url=f"https://github.com/{owner}/{repo}/pull/{self._pr_counter}",
            branch_name=head_branch,
        )
        self.created_pull_requests.append(pull_request)
        return pull_request

    async def get_pull_request(
        self, *, owner: str, repo: str, pr_number: int
    ) -> PullRequestDetailDTO:
        pr = self._pull_requests.get((owner, repo, pr_number))
        if pr is None:
            raise FileNotFoundError(f"{owner}/{repo}#{pr_number} not seeded in mock write client")
        return pr

    async def get_pull_request_files(
        self, *, owner: str, repo: str, pr_number: int
    ) -> list[PullRequestFileDTO]:
        files = self._pull_request_files.get((owner, repo, pr_number))
        if files is None:
            raise FileNotFoundError(f"{owner}/{repo}#{pr_number} not seeded in mock write client")
        return files

    async def create_review(
        self,
        *,
        owner: str,
        repo: str,
        pr_number: int,
        commit_sha: str,
        body: str,
        comments: list[ReviewCommentDTO],
    ) -> ReviewResultDTO:
        self._review_counter += 1
        review_id = self._review_counter
        self.created_reviews.append(
            {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "body": body,
                "comments": comments,
            }
        )
        return ReviewResultDTO(
            id=review_id,
            html_url=f"https://github.com/{owner}/{repo}/pull/{pr_number}#pullrequestreview-{review_id}",
        )

    async def create_commit_status(
        self,
        *,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str,
        context: str,
    ) -> None:
        self.created_commit_statuses.append(
            {
                "owner": owner,
                "repo": repo,
                "sha": sha,
                "state": state,
                "description": description,
                "context": context,
            }
        )
