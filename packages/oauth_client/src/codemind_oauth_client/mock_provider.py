from codemind_oauth_client.interface import OAuthProvider
from codemind_shared_types.schemas import OAuthUserInfoDTO


class MockOAuthProvider(OAuthProvider):
    """Returns a canned user for a given code, deterministic for tests. Never
    used outside pytest — real requests always resolve a real provider or 501."""

    def __init__(self, *, user: OAuthUserInfoDTO | None = None) -> None:
        self._user = user or OAuthUserInfoDTO(
            email="oauth-user@example.com",
            provider_user_id="mock-provider-user-id",
            full_name="Mock OAuth User",
            access_token="mock-access-token",
            username="mock-oauth-user",
        )

    def authorize_url(self, *, state: str, scope: str | None = None) -> str:
        return f"https://mock-oauth.example.com/authorize?state={state}"

    async def exchange_code(self, *, code: str) -> OAuthUserInfoDTO:
        return self._user
