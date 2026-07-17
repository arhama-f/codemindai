from httpx import AsyncClient


async def test_register_creates_user_and_session_cookie(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "hunter2", "full_name": "Ada Lovelace"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["full_name"] == "Ada Lovelace"
    assert "codemind_session" in response.cookies


async def test_register_duplicate_email_is_conflict(client: AsyncClient):
    payload = {"email": "grace@example.com", "password": "hunter2", "full_name": "Grace Hopper"}
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_with_wrong_password_is_unauthorized(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "alan@example.com", "password": "correct-horse", "full_name": "Alan Turing"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": "alan@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_login_with_correct_credentials_succeeds(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "margaret@example.com", "password": "s3cret", "full_name": "Margaret Hamilton"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": "margaret@example.com", "password": "s3cret"}
    )
    assert response.status_code == 200
    assert "codemind_session" in response.cookies


async def test_me_requires_authentication(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user_after_register(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "hedy@example.com", "password": "frequency-hop", "full_name": "Hedy Lamarr"},
    )
    response = await client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "hedy@example.com"


async def test_logout_clears_session_cookie(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "katherine@example.com", "password": "trajectory", "full_name": "Katherine Johnson"},
    )
    response = await client.post("/api/auth/logout")
    assert response.status_code == 204
