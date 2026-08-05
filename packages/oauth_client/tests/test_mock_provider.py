from codemind_oauth_client import MockOAuthProvider
from codemind_shared_types.schemas import OAuthUserInfoDTO


async def test_mock_provider_returns_canned_user():
    provider = MockOAuthProvider()

    user = await provider.exchange_code(code="anything")

    assert user.email == "oauth-user@example.com"
    assert user.provider_user_id == "mock-provider-user-id"


async def test_mock_provider_authorize_url_includes_state():
    provider = MockOAuthProvider()

    url = provider.authorize_url(state="xyz123")

    assert "state=xyz123" in url


async def test_mock_provider_accepts_custom_user():
    custom = OAuthUserInfoDTO(email="custom@example.com", provider_user_id="custom-id")
    provider = MockOAuthProvider(user=custom)

    user = await provider.exchange_code(code="anything")

    assert user.email == "custom@example.com"
