import base64
from collections.abc import Awaitable, Callable

import httpx

from codemind_github_client.interface import GitHubClient
from codemind_shared_types.schemas import (
    BranchDTO,
    CommitDTO,
    FileContentDTO,
    InstallationDTO,
    RepositoryDTO,
    RepositorySnapshot,
)

GITHUB_API_BASE = "https://api.github.com"
PARSEABLE_EXTENSIONS = (".ts", ".tsx")
MAX_REPO_PAGES = 10


class OAuthTokenGitHubClient(GitHubClient):
    """Real GitHub client backed by a per-installation OAuth user access
    token (not a GitHub App installation — see docs/architecture.md). Since
    the ABC's methods only take opaque IDs, the access token for a given
    `installation_id` is resolved via an injected callback rather than a
    direct DB import, keeping this package free of any apps.api dependency.
    """

    def __init__(self, *, resolve_access_token: Callable[[str], Awaitable[str]]) -> None:
        self._resolve_access_token = resolve_access_token

    async def list_installations(self, *, user_id: str) -> list[InstallationDTO]:
        raise NotImplementedError(
            "OAuthTokenGitHubClient has no installation concept — the "
            "github_connect callback route creates GithubInstallation rows "
            "directly and never calls this method."
        )

    async def list_repositories(self, *, installation_id: str) -> list[RepositoryDTO]:
        token = await self._resolve_access_token(installation_id)
        headers = _headers(token)
        repos: list[RepositoryDTO] = []

        async with httpx.AsyncClient() as client:
            for page in range(1, MAX_REPO_PAGES + 1):
                response = await client.get(
                    f"{GITHUB_API_BASE}/user/repos",
                    headers=headers,
                    params={
                        "per_page": 100,
                        "page": page,
                        "affiliation": "owner,collaborator,organization_member",
                    },
                )
                response.raise_for_status()
                data = response.json()
                repos.extend(
                    RepositoryDTO(
                        external_repo_id=str(item["id"]),
                        full_name=item["full_name"],
                        default_branch=item["default_branch"],
                    )
                    for item in data
                )
                if len(data) < 100:
                    break

        return repos

    async def get_repository_snapshot(
        self, *, installation_id: str, external_repo_id: str
    ) -> RepositorySnapshot:
        token = await self._resolve_access_token(installation_id)
        headers = _headers(token)

        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"{GITHUB_API_BASE}/repositories/{external_repo_id}", headers=headers
            )
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            owner = repo_data["owner"]["login"]
            repo = repo_data["name"]
            default_branch = repo_data["default_branch"]

            commit_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{default_branch}",
                headers=headers,
            )
            commit_response.raise_for_status()
            commit_data = commit_response.json()
            commit_author = commit_data["commit"]["author"]

            tree_response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{commit_data['sha']}",
                headers=headers,
                params={"recursive": "1"},
            )
            tree_response.raise_for_status()
            tree_entries = tree_response.json()["tree"]

            files: list[FileContentDTO] = []
            for entry in tree_entries:
                if entry["type"] != "blob" or not entry["path"].endswith(PARSEABLE_EXTENSIONS):
                    continue
                blob_response = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/blobs/{entry['sha']}",
                    headers=headers,
                )
                blob_response.raise_for_status()
                blob_data = blob_response.json()
                content = base64.b64decode(blob_data["content"]).decode("utf-8")
                files.append(FileContentDTO(path=entry["path"], content=content))

        return RepositorySnapshot(
            branch=BranchDTO(name=default_branch, is_default=True),
            commit=CommitDTO(
                sha=commit_data["sha"],
                message=commit_data["commit"]["message"],
                author_name=commit_author["name"],
                author_email=commit_author["email"],
                committed_at=commit_author["date"],
            ),
            files=files,
        )


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
