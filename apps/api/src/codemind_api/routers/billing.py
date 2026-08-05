from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codemind_api.config import settings
from codemind_api.db import get_db
from codemind_api.deps import get_org_membership
from codemind_api.plan_limits import PLAN_LIMITS, count_ai_actions_this_month, count_repositories
from codemind_shared_types.models import Organization, Subscription

router = APIRouter(prefix="/api/organizations/{org_id}/billing", tags=["billing"])

_PRICE_IDS_BY_PLAN = {
    "pro": lambda: settings.stripe_price_id_pro,
    "team": lambda: settings.stripe_price_id_team,
}


class UsageDimension(BaseModel):
    used: int
    limit: int | None


class BillingResponse(BaseModel):
    plan: str
    status: str
    usage: dict[str, UsageDimension]


class CheckoutResponse(BaseModel):
    url: str


async def _get_or_create_subscription(db: AsyncSession, org_id: UUID) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.organization_id == org_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        subscription = Subscription(organization_id=org_id, plan="free", status="active")
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
    return subscription


@router.get("", response_model=BillingResponse)
async def get_billing(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> BillingResponse:
    subscription = await _get_or_create_subscription(db, org_id)
    limits = PLAN_LIMITS[subscription.plan]

    return BillingResponse(
        plan=subscription.plan,
        status=subscription.status,
        usage={
            "repositories": UsageDimension(
                used=await count_repositories(db, org_id), limit=limits["repositories"]
            ),
            "ai_actions_per_month": UsageDimension(
                used=await count_ai_actions_this_month(db, org_id),
                limit=limits["ai_actions_per_month"],
            ),
        },
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    org_id: UUID,
    plan: str,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> CheckoutResponse:
    if not settings.stripe_secret_key:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="Billing is not configured")
    if plan not in _PRICE_IDS_BY_PLAN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown plan")
    price_id = _PRICE_IDS_BY_PLAN[plan]()
    if not price_id:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail=f"No Stripe price configured for {plan}")

    organization = await db.get(Organization, org_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Organization not found")
    subscription = await _get_or_create_subscription(db, org_id)

    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer=subscription.stripe_customer_id,
        client_reference_id=str(org_id),
        success_url=f"{settings.web_origin}/orgs/{org_id}/billing?checkout=success",
        cancel_url=f"{settings.web_origin}/orgs/{org_id}/billing?checkout=canceled",
    )
    return CheckoutResponse(url=session.url)


@router.post("/portal", response_model=CheckoutResponse)
async def create_portal_session(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(get_org_membership),
) -> CheckoutResponse:
    if not settings.stripe_secret_key:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail="Billing is not configured")

    subscription = await _get_or_create_subscription(db, org_id)
    if not subscription.stripe_customer_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="No Stripe customer on file for this organization"
        )

    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=f"{settings.web_origin}/orgs/{org_id}/billing",
    )
    return CheckoutResponse(url=session.url)
