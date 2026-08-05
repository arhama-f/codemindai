import stripe
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_shared_types.models import Subscription


async def _org(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "hunter2", "full_name": "Test User"},
    )
    created = await client.post("/api/organizations", json={"name": "Billing Org"})
    return created.json()["id"]


async def test_checkout_without_stripe_configured_returns_501(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", None)
    org_id = await _org(client, "checkout-unconfigured@example.com")

    response = await client.post(f"/api/organizations/{org_id}/billing/checkout?plan=pro")
    assert response.status_code == 501


async def test_portal_without_stripe_configured_returns_501(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", None)
    org_id = await _org(client, "portal-unconfigured@example.com")

    response = await client.post(f"/api/organizations/{org_id}/billing/portal")
    assert response.status_code == 501


async def test_checkout_with_unknown_plan_is_bad_request(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_123")
    org_id = await _org(client, "checkout-unknown-plan@example.com")

    response = await client.post(f"/api/organizations/{org_id}/billing/checkout?plan=enterprise")
    assert response.status_code == 400


async def test_checkout_creates_a_session_when_configured(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_123")
    monkeypatch.setattr(settings, "stripe_price_id_pro", "price_pro_123")

    class _FakeSession:
        url = "https://checkout.stripe.com/fake-session"

    monkeypatch.setattr(stripe.checkout.Session, "create", lambda **kwargs: _FakeSession())

    org_id = await _org(client, "checkout-ok@example.com")
    response = await client.post(f"/api/organizations/{org_id}/billing/checkout?plan=pro")
    assert response.status_code == 200
    assert response.json()["url"] == "https://checkout.stripe.com/fake-session"


async def test_portal_requires_an_existing_stripe_customer(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_123")
    org_id = await _org(client, "portal-no-customer@example.com")

    response = await client.post(f"/api/organizations/{org_id}/billing/portal")
    assert response.status_code == 400


async def test_portal_creates_a_session_for_an_existing_customer(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_123")
    org_id = await _org(client, "portal-ok@example.com")

    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    subscription = result.scalar_one()
    subscription.stripe_customer_id = "cus_123"
    await db_session.commit()

    class _FakeSession:
        url = "https://billing.stripe.com/fake-portal"

    monkeypatch.setattr(stripe.billing_portal.Session, "create", lambda **kwargs: _FakeSession())

    response = await client.post(f"/api/organizations/{org_id}/billing/portal")
    assert response.status_code == 200
    assert response.json()["url"] == "https://billing.stripe.com/fake-portal"
