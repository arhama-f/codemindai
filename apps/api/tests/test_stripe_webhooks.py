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
    created = await client.post("/api/organizations", json={"name": "Webhook Org"})
    return created.json()["id"]


async def _subscription(db_session: AsyncSession, org_id: str) -> Subscription:
    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    return result.scalar_one()


async def test_webhook_without_secret_configured_returns_501(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", None)

    response = await client.post(
        "/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "x"}
    )
    assert response.status_code == 501


async def test_webhook_with_invalid_signature_returns_400(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")

    def _raise(*args, **kwargs):
        raise stripe.error.SignatureVerificationError("bad signature", "sig_header")

    monkeypatch.setattr(stripe.Webhook, "construct_event", _raise)

    response = await client.post(
        "/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "bad"}
    )
    assert response.status_code == 400


async def test_checkout_completed_sets_customer_subscription_and_plan(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr(settings, "stripe_price_id_pro", "price_pro_123")
    org_id = await _org(client, "webhook-checkout@example.com")

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": org_id,
                "customer": "cus_abc",
                "subscription": "sub_abc",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: event)
    monkeypatch.setattr(
        stripe.Subscription,
        "retrieve",
        lambda sub_id: {"status": "active", "items": {"data": [{"price": {"id": "price_pro_123"}}]}},
    )

    response = await client.post(
        "/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
    )
    assert response.status_code == 204

    subscription = await _subscription(db_session, org_id)
    assert subscription.plan == "pro"
    assert subscription.status == "active"
    assert subscription.stripe_customer_id == "cus_abc"
    assert subscription.stripe_subscription_id == "sub_abc"


async def test_subscription_updated_changes_plan_and_status(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr(settings, "stripe_price_id_team", "price_team_456")
    org_id = await _org(client, "webhook-updated@example.com")

    subscription = await _subscription(db_session, org_id)
    subscription.stripe_customer_id = "cus_xyz"
    subscription.stripe_subscription_id = "sub_xyz"
    await db_session.commit()

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_xyz",
                "customer": "cus_xyz",
                "status": "past_due",
                "items": {"data": [{"price": {"id": "price_team_456"}}]},
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: event)

    response = await client.post(
        "/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
    )
    assert response.status_code == 204

    updated = await _subscription(db_session, org_id)
    assert updated.plan == "team"
    assert updated.status == "past_due"


async def test_subscription_deleted_resets_to_free(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    org_id = await _org(client, "webhook-deleted@example.com")

    subscription = await _subscription(db_session, org_id)
    subscription.plan = "pro"
    subscription.stripe_customer_id = "cus_del"
    subscription.stripe_subscription_id = "sub_del"
    await db_session.commit()

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_del", "customer": "cus_del"}},
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: event)

    response = await client.post(
        "/api/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
    )
    assert response.status_code == 204

    updated = await _subscription(db_session, org_id)
    assert updated.plan == "free"
    assert updated.status == "canceled"
