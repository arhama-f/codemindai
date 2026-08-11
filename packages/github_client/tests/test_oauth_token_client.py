import pytest

from codemind_github_client.oauth_token_client import OAuthTokenGitHubClient, _headers


async def test_list_installations_is_not_implemented():
    """The OAuth-token flow has no real "installation" concept — the
    github_connect callback route creates GithubInstallation rows directly
    and never calls this method. See docs/architecture.md."""
    client = OAuthTokenGitHubClient(resolve_access_token=lambda installation_id: "unused")

    with pytest.raises(NotImplementedError):
        await client.list_installations(user_id="any-user")


def test_headers_shape():
    headers = _headers("a-real-token")

    assert headers["Authorization"] == "Bearer a-real-token"
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"


async def test_list_repositories_resolves_token_via_injected_callback():
    """Confirms the constructor's injected resolver is actually invoked with
    the installation_id argument, without making a real network call — the
    resolver here returns an invalid token so the real httpx call fails fast,
    which is enough to prove resolution happened before any request went out."""
    seen_installation_ids: list[str] = []

    async def resolve(installation_id: str) -> str:
        seen_installation_ids.append(installation_id)
        raise RuntimeError("stop before any real network call")

    client = OAuthTokenGitHubClient(resolve_access_token=resolve)

    with pytest.raises(RuntimeError, match="stop before any real network call"):
        await client.list_repositories(installation_id="some-installation-id")

    assert seen_installation_ids == ["some-installation-id"]
