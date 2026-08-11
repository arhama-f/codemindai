import httpx

from codemind_oauth_client.interface import OAuthProvider
from codemind_shared_types.schemas import OAuthUserInfoDTO

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"
EMAILS_URL = "https://api.github.com/user/emails"


class GitHubOAuthProvider(OAuthProvider):
    """Real GitHub OAuth2 authorization-code flow (login only — distinct from
    packages/github_client, which is the read/write GitHub API client for
    indexing and publishing). Never exercised by the automated test suite;
    only used once GITHUB_OAUTH_CLIENT_ID/SECRET are configured."""

    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def authorize_url(self, *, state: str, scope: str | None = None) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": scope or "read:user user:email",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{AUTHORIZE_URL}?{query}"

    async def exchange_code(self, *, code: str) -> OAuthUserInfoDTO:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}

            user_response = await client.get(USER_URL, headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()

            email = user_data.get("email")
            if email is None:
                emails_response = await client.get(EMAILS_URL, headers=headers)
                emails_response.raise_for_status()
                primary = next(
                    (e for e in emails_response.json() if e.get("primary")), None
                )
                email = primary["email"] if primary else emails_response.json()[0]["email"]

        return OAuthUserInfoDTO(
            email=email,
            provider_user_id=str(user_data["id"]),
            full_name=user_data.get("name"),
            access_token=access_token,
            username=user_data.get("login"),
        )
