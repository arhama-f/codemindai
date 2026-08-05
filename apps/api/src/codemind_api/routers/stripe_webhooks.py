import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_shared_types.models import Subscription

router = APIRouter(prefix="/api/webhooks/stripe", tags=["billing"])


def _plan_from_price_id(price_id: str | None) -> str | None:
    if price_id and price_id == settings.stripe_price_id_pro:
        return "pro"
    if price_id and price_id == settings.stripe_price_id_team:
        return "team"
    return None


async def _get_subscription_by_stripe_ids(
    db: AsyncSession, *, org_id: str | None, customer_id: str | None, subscription_id: str | None
) -> Subscription | None:
    if subscription_id:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
        )
        found = result.scalar_one_or_none()
        if found is not None:
            return found
    if org_id:
        result = await db.execute(select(Subscription).where(Subscription.organization_id == org_id))
        found = result.scalar_one_or_none()
        if found is not None:
            return found
    if customer_id:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()
    return None


async def _handle_checkout_completed(db: AsyncSession, session: dict) -> None:
    subscription = await _get_subscription_by_stripe_ids(
        db,
        org_id=session.get("client_reference_id"),
        customer_id=session.get("customer"),
        subscription_id=None,
    )
    if subscription is None:
        return

    stripe_subscription = stripe.Subscription.retrieve(session["subscription"])
    price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
    plan = _plan_from_price_id(price_id)

    subscription.stripe_customer_id = session.get("customer")
    subscription.stripe_subscription_id = session.get("subscription")
    subscription.status = stripe_subscription["status"]
    if plan:
        subscription.plan = plan
    await db.commit()


async def _handle_subscription_updated(db: AsyncSession, stripe_subscription: dict) -> None:
    subscription = await _get_subscription_by_stripe_ids(
        db,
        org_id=None,
        customer_id=stripe_subscription.get("customer"),
        subscription_id=stripe_subscription.get("id"),
    )
    if subscription is None:
        return

    price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
    plan = _plan_from_price_id(price_id)

    subscription.stripe_subscription_id = stripe_subscription["id"]
    subscription.status = stripe_subscription["status"]
    if plan:
        subscription.plan = plan
    await db.commit()


async def _handle_subscription_deleted(db: AsyncSession, stripe_subscription: dict) -> None:
    subscription = await _get_subscription_by_stripe_ids(
        db,
        org_id=None,
        customer_id=stripe_subscription.get("customer"),
        subscription_id=stripe_subscription.get("id"),
    )
    if subscription is None:
        return

    subscription.status = "canceled"
    subscription.plan = "free"
    await db.commit()


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    if not settings.stripe_webhook_secret:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="Billing is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload") from exc

    event_type = event["type"]
    data = event["data"]["object"]
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)
