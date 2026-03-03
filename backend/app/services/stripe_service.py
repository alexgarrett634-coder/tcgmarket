"""Stripe subscription, Connect, and marketplace integration."""
import stripe
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.config import settings
from app.models.subscription import Subscription
from app.models.wallet import Wallet, WalletTransaction
from app.models.wallet import KycVerification

stripe.api_key = settings.stripe_secret_key


# ─── Stripe Connect (Seller onboarding) ────────────────────────────────────────

async def create_seller_account(user_id: int, return_url: str, refresh_url: str) -> dict:
    """Create a Stripe Express account and return the onboarding URL."""
    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe is not configured. Add STRIPE_SECRET_KEY to .env")
    account = stripe.Account.create(type="express", metadata={"user_id": str(user_id)})
    account_link = stripe.AccountLink.create(
        account=account.id,
        return_url=return_url,
        refresh_url=refresh_url,
        type="account_onboarding",
    )
    return {"stripe_account_id": account.id, "onboarding_url": account_link.url}


async def get_seller_dashboard_link(stripe_account_id: str, return_url: str) -> str:
    """Return a Stripe Express dashboard login link URL."""
    link = stripe.Account.create_login_link(stripe_account_id, redirect_url=return_url)
    return link.url


# ─── Wallet deposit ────────────────────────────────────────────────────────────

async def create_wallet_deposit_intent(user_id: int, amount_usd: float, stripe_customer_id: str) -> dict:
    """Create a PaymentIntent for a wallet top-up. Returns client_secret."""
    if amount_usd < 5.0:
        raise HTTPException(400, "Minimum deposit is $5.00")
    intent = stripe.PaymentIntent.create(
        amount=int(amount_usd * 100),
        currency="usd",
        customer=stripe_customer_id if not stripe_customer_id.startswith("cus_pending_") else None,
        metadata={"user_id": str(user_id), "type": "wallet_deposit"},
    )
    return {"client_secret": intent.client_secret, "amount": amount_usd}


# ─── Subscription checkout ──────────────────────────────────────────────────────

async def create_checkout_session(user_id: int, tier: str, stripe_customer_id: str) -> str:
    """Create a Stripe Checkout Session for a subscription. Returns URL."""
    if tier == "enterprise":
        price_id = settings.stripe_enterprise_price_id
    elif tier == "insights":
        price_id = settings.stripe_insights_price_id
    else:
        price_id = settings.stripe_pro_price_id
    if not price_id:
        raise HTTPException(503, "Stripe is not configured")

    session = stripe.checkout.Session.create(
        customer=stripe_customer_id if not stripe_customer_id.startswith("cus_pending_") else None,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/billing?success=1",
        cancel_url=f"{settings.frontend_url}/billing?cancelled=1",
        metadata={"user_id": str(user_id), "tier": tier},
    )
    return session.url


async def create_portal_session(stripe_customer_id: str) -> str:
    """Return Stripe Customer Portal URL for self-serve subscription management."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/billing",
    )
    return session.url


# ─── Webhook handler ────────────────────────────────────────────────────────────

async def handle_webhook(db: AsyncSession, payload: bytes, sig_header: str) -> None:
    """Process Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid webhook signature")

    etype = event["type"]
    data = event["data"]["object"]

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        await _handle_subscription_update(db, data)
    elif etype == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)
    elif etype == "payment_intent.succeeded":
        await _handle_payment_success(db, data)
    elif etype == "account.updated":
        await _handle_account_updated(db, data)


async def _handle_subscription_update(db: AsyncSession, sub: dict) -> None:
    customer_id = sub["customer"]
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        return

    price_id = sub["items"]["data"][0]["price"]["id"] if sub.get("items") else None
    if price_id == settings.stripe_enterprise_price_id:
        tier = "enterprise"
    elif price_id == settings.stripe_pro_price_id:
        tier = "pro"
    elif price_id and settings.stripe_insights_price_id and price_id == settings.stripe_insights_price_id:
        tier = "insights"
    else:
        tier = "free"

    subscription.tier = tier
    subscription.stripe_subscription_id = sub["id"]
    subscription.status = sub["status"]
    period_end = sub.get("current_period_end")
    if period_end:
        subscription.current_period_end = datetime.utcfromtimestamp(period_end)
    subscription.updated_at = datetime.utcnow()
    await db.commit()


async def _handle_subscription_deleted(db: AsyncSession, sub: dict) -> None:
    customer_id = sub["customer"]
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription:
        subscription.tier = "free"
        subscription.status = "canceled"
        subscription.updated_at = datetime.utcnow()
        await db.commit()


async def _handle_payment_success(db: AsyncSession, intent: dict) -> None:
    """Route payment success to the correct handler based on type metadata."""
    meta = intent.get("metadata", {})
    intent_type = meta.get("type")

    if intent_type == "listing_purchase":
        from app.services.order_service import handle_payment_succeeded
        await handle_payment_succeeded(db, intent)
    elif intent_type == "wallet_deposit":
        user_id = int(meta.get("user_id", 0))
        amount_usd = intent.get("amount", 0) / 100.0
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if wallet:
            wallet.real_credits_usd += amount_usd
            wallet.updated_at = datetime.utcnow()
            db.add(WalletTransaction(
                user_id=user_id,
                type="deposit",
                currency="usd",
                amount=amount_usd,
                note=f"Stripe deposit (PI {intent['id']})",
            ))
            await db.commit()


async def _handle_account_updated(db: AsyncSession, account: dict) -> None:
    """Mark seller as onboarding_complete when Stripe confirms their account."""
    from app.models.listing import SellerProfile
    if not account.get("details_submitted"):
        return
    user_id_str = account.get("metadata", {}).get("user_id")
    if not user_id_str:
        return
    result = await db.execute(
        select(SellerProfile).where(SellerProfile.user_id == int(user_id_str))
    )
    profile = result.scalar_one_or_none()
    if profile:
        profile.onboarding_complete = True
        profile.stripe_account_id = account["id"]
        profile.updated_at = datetime.utcnow()
        await db.commit()
