from httpx import AsyncClient


def _extract_token(html_body: str, path_segment: str) -> str:
    return html_body.split(f"{path_segment}/")[1].split('"')[0]


async def test_request_password_reset_for_existing_email_sends_link(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "rosalind@example.com", "password": "old-pass", "full_name": "Rosalind Franklin"},
    )
    sent_before = len(client.email_provider.sent)

    response = await client.post(
        "/api/auth/request-password-reset", json={"email": "rosalind@example.com"}
    )
    assert response.status_code == 204
    assert len(client.email_provider.sent) == sent_before + 1


async def test_request_password_reset_for_unknown_email_is_still_204(client: AsyncClient):
    response = await client.post(
        "/api/auth/request-password-reset", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 204


async def test_reset_password_with_valid_token_allows_new_login(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "barbara@example.com", "password": "old-pass", "full_name": "Barbara McClintock"},
    )
    await client.post("/api/auth/request-password-reset", json={"email": "barbara@example.com"})
    token = _extract_token(client.email_provider.sent[-1]["html_body"], "/reset-password")

    reset_response = await client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "new-pass"}
    )
    assert reset_response.status_code == 204

    old_login = await client.post(
        "/api/auth/login", json={"email": "barbara@example.com", "password": "old-pass"}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/auth/login", json={"email": "barbara@example.com", "password": "new-pass"}
    )
    assert new_login.status_code == 200


async def test_reset_password_with_invalid_token_is_bad_request(client: AsyncClient):
    response = await client.post(
        "/api/auth/reset-password", json={"token": "not-a-real-token", "new_password": "new-pass"}
    )
    assert response.status_code == 400


async def test_reset_password_token_cannot_be_reused(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "jocelyn@example.com", "password": "old-pass", "full_name": "Jocelyn Bell Burnell"},
    )
    await client.post("/api/auth/request-password-reset", json={"email": "jocelyn@example.com"})
    token = _extract_token(client.email_provider.sent[-1]["html_body"], "/reset-password")

    first = await client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "new-pass-1"}
    )
    assert first.status_code == 204
    second = await client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "new-pass-2"}
    )
    assert second.status_code == 400
