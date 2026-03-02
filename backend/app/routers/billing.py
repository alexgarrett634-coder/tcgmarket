from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.services.stripe_service import (
    create_checkout_session,
    create_portal_session,
    handle_webhook,
)
from app.config import settings

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tier: str  # "pro" or "enterprise"


@router.post("/checkout")
async def checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.tier not in ("pro", "enterprise"):
        raise HTTPException(400, "tier must be 'pro' or 'enterprise'")

    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(400, "Subscription record not found")

    url = await create_checkout_session(current_user.id, body.tier, sub.stripe_customer_id)
    return {"url": url}


@router.post("/portal")
async def customer_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = result.scalar_one_or_none()
    if not sub or sub.stripe_customer_id.startswith("cus_pending_"):
        raise HTTPException(400, "No active Stripe customer. Please subscribe first.")
    url = await create_portal_session(sub.stripe_customer_id)
    return {"url": url}


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = result.scalar_one_or_none()
    if not sub:
        return {"tier": "free", "status": "active"}
    return {
        "tier": sub.tier,
        "status": sub.status,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    await handle_webhook(db, payload, sig)
    return {"received": True}
