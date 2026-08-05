from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient


def _extract_state(location: str) -> str:
    return parse_qs(urlparse(location).query)["state"][0]


async def test_oauth_start_redirects_and_sets_state_cookie(client: AsyncClient):
    response = await client.get("/api/auth/oauth/google/start", follow_redirects=False)
    assert response.status_code == 302
    assert "oauth_state" in response.cookies
    assert "state=" in response.headers["location"]


async def test_oauth_callback_with_mismatched_state_is_bad_request(client: AsyncClient):
    await client.get("/api/auth/oauth/google/start", follow_redirects=False)
    response = await client.get(
        "/api/auth/oauth/google/callback",
        params={"code": "any-code", "state": "wrong-state"},
        follow_redirects=False,
    )
    assert response.status_code == 400


async def test_oauth_callback_creates_new_verified_user_and_session(client: AsyncClient):
    start = await client.get("/api/auth/oauth/google/start", follow_redirects=False)
    state = _extract_state(start.headers["location"])

    callback = await client.get(
        "/api/auth/oauth/google/callback",
        params={"code": "any-code", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["location"].endswith("/orgs")
    assert "codemind_session" in callback.cookies

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "oauth-user@example.com"
    assert me.json()["is_verified"] is True


async def test_oauth_callback_links_existing_email_password_account(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "email": "oauth-user@example.com",
            "password": "hunter2",
            "full_name": "Existing User",
        },
    )
    await client.post("/api/auth/logout")

    start = await client.get("/api/auth/oauth/google/start", follow_redirects=False)
    state = _extract_state(start.headers["location"])

    callback = await client.get(
        "/api/auth/oauth/google/callback",
        params={"code": "any-code", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 302

    me = await client.get("/api/auth/me")
    assert me.json()["full_name"] == "Existing User"
