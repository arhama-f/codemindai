import base64

import httpx

from codemind_github_client.write_interface import GitHubWriteClient
from codemind_shared_types.schemas import (
    PullRequestDetailDTO,
    PullRequestDTO,
    PullRequestFileDTO,
    RemoteFileDTO,
    ReviewCommentDTO,
    ReviewResultDTO,
)

GITHUB_API_BASE = "https://api.github.com"


class PATGitHubWriteClient(GitHubWriteClient):
    """Real GitHub write client using a personal access token against the
    REST API directly (no GitHub App, no webhooks — see docs/architecture.md
    for why). Never exercised by the automated test suite; only used in the
    round 4 plan's final manual real-credentials verification step."""

    def __init__(self, *, token: str) -> None:
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_file(self, *, owner: str, repo: str, path: str, branch: str) -> RemoteFileDTO:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
                headers=self._headers,
            )
            response.raise_for_status()
            data = response.json()

        content = base64.b64decode(data["content"]).decode("utf-8")
        return RemoteFileDTO(path=data["path"], sha=data["sha"], content=content)

    async def create_branch(
        self, *, owner: str, repo: str, base_branch: str, new_branch: str
    ) -> None:
        async with httpx.AsyncClient() as client:
            ref_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/ref/heads/{base_branch}",
                headers=self._headers,
            )
            ref_response.raise_for_status()
            base_sha = ref_response.json()["object"]["sha"]

            create_response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/refs",
                headers=self._headers,
                json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
            )
            create_response.raise_for_status()

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
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload = {"message": message, "content": encoded_content, "branch": branch}
        if sha is not None:
            payload["sha"] = sha
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                headers=self._headers,
                json={
                    "title": title,
                    "head": head_branch,
                    "base": base_branch,
                    "body": body,
                    "draft": draft,
                },
            )
            response.raise_for_status()
            data = response.json()

        return PullRequestDTO(
            number=data["number"], url=data["html_url"], branch_name=head_branch
        )

    async def get_pull_request(
        self, *, owner: str, repo: str, pr_number: int
    ) -> PullRequestDetailDTO:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self._headers,
            )
            response.raise_for_status()
            data = response.json()

        return PullRequestDetailDTO(
            number=data["number"],
            title=data["title"],
            head_sha=data["head"]["sha"],
            head_ref=data["head"]["ref"],
            base_ref=data["base"]["ref"],
        )

    async def get_pull_request_files(
        self, *, owner: str, repo: str, pr_number: int
    ) -> list[PullRequestFileDTO]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers=self._headers,
            )
            response.raise_for_status()
            data = response.json()

        return [
            PullRequestFileDTO(path=f["filename"], status=f["status"], patch=f.get("patch"))
            for f in data
        ]

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                headers=self._headers,
                json={
                    "commit_id": commit_sha,
                    "body": body,
                    "event": "COMMENT",
                    "comments": [
                        {"path": c.path, "line": c.line, "side": "RIGHT", "body": c.body}
                        for c in comments
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()

        return ReviewResultDTO(id=data["id"], html_url=data["html_url"])

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/statuses/{sha}",
                headers=self._headers,
                json={"state": state, "description": description, "context": context},
            )
            response.raise_for_status()
