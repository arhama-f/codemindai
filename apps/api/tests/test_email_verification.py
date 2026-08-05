from httpx import AsyncClient


def _extract_token(html_body: str, path_segment: str) -> str:
    return html_body.split(f"{path_segment}/")[1].split('"')[0]


async def test_register_sends_verification_email_and_user_starts_unverified(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "vera@example.com", "password": "hunter2", "full_name": "Vera Rubin"},
    )
    assert response.status_code == 201
    assert response.json()["is_verified"] is False
    assert len(client.email_provider.sent) == 1
    assert client.email_provider.sent[0]["to"] == "vera@example.com"


async def test_verify_email_with_valid_token_marks_user_verified(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "mae@example.com", "password": "hunter2", "full_name": "Mae Jemison"},
    )
    token = _extract_token(client.email_provider.sent[0]["html_body"], "/verify-email")

    response = await client.get(f"/api/auth/verify-email/{token}")
    assert response.status_code == 200
    assert response.json()["verified"] is True

    me = await client.get("/api/auth/me")
    assert me.json()["is_verified"] is True


async def test_verify_email_with_invalid_token_is_bad_request(client: AsyncClient):
    response = await client.get("/api/auth/verify-email/not-a-real-token")
    assert response.status_code == 400


async def test_verify_email_token_cannot_be_reused(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "sally@example.com", "password": "hunter2", "full_name": "Sally Ride"},
    )
    token = _extract_token(client.email_provider.sent[0]["html_body"], "/verify-email")

    first = await client.get(f"/api/auth/verify-email/{token}")
    assert first.status_code == 200
    second = await client.get(f"/api/auth/verify-email/{token}")
    assert second.status_code == 400


async def test_resend_verification_requires_authentication(client: AsyncClient):
    response = await client.post("/api/auth/resend-verification")
    assert response.status_code == 401


async def test_resend_verification_sends_another_email(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "chien@example.com", "password": "hunter2", "full_name": "Chien-Shiung Wu"},
    )
    assert len(client.email_provider.sent) == 1

    response = await client.post("/api/auth/resend-verification")
    assert response.status_code == 204
    assert len(client.email_provider.sent) == 2
