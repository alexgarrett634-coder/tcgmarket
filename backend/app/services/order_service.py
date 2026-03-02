"""Order creation and lifecycle management."""
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.order import Order
from app.models.listing import Listing, SellerProfile
from app.models.wallet import WalletTransaction

COMMISSION_RATE = 0.06


async def create_order(
    db: AsyncSession,
    buyer_id: int,
    listing_id: int,
    quantity: int,
    shipping_address: dict,
) -> dict:
    """Create an Order + Stripe PaymentIntent. Returns {order_id, client_secret}."""
    import stripe
    from app.config import settings
    stripe.api_key = settings.stripe_secret_key

    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.status != "active":
        raise HTTPException(400, "This listing is no longer available")
    if listing.seller_id == buyer_id:
        raise HTTPException(400, "You cannot buy your own listing")
    if quantity > listing.quantity:
        raise HTTPException(400, f"Only {listing.quantity} available")

    # Get seller's Stripe Connect account
    sp_result = await db.execute(
        select(SellerProfile).where(SellerProfile.user_id == listing.seller_id)
    )
    seller_profile = sp_result.scalar_one_or_none()
    if not seller_profile or not seller_profile.onboarding_complete:
        raise HTTPException(400, "Seller has not completed payment setup")

    subtotal = round(listing.price * quantity, 2)
    commission_amount = round(subtotal * COMMISSION_RATE, 2)
    payout_amount = round(subtotal - commission_amount, 2)

    order = Order(
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        listing_id=listing_id,
        quantity=quantity,
        price_each=listing.price,
        subtotal=subtotal,
        commission_rate=COMMISSION_RATE,
        commission_amount=commission_amount,
        payout_amount=payout_amount,
        shipping_address=json.dumps(shipping_address),
        status="pending",
    )
    db.add(order)
    await db.flush()  # get order.id

    # Create Stripe PaymentIntent with destination charge
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(subtotal * 100),
            currency="usd",
            transfer_data={
                "destination": seller_profile.stripe_account_id,
                "amount": int(payout_amount * 100),
            },
            metadata={
                "order_id": str(order.id),
                "type": "listing_purchase",
                "buyer_id": str(buyer_id),
                "seller_id": str(listing.seller_id),
            },
        )
        order.stripe_payment_intent_id = intent.id
    except Exception as e:
        # If Stripe isn't configured, return a test-mode client_secret placeholder
        order.stripe_payment_intent_id = f"pi_test_{order.id}"
        await db.commit()
        return {"order_id": order.id, "client_secret": None, "test_mode": True,
                "message": "Stripe not configured — order created in test mode"}

    await db.commit()
    return {"order_id": order.id, "client_secret": intent.client_secret}


async def handle_payment_succeeded(db: AsyncSession, payment_intent: dict) -> None:
    """Called from Stripe webhook when listing_purchase PaymentIntent succeeds."""
    meta = payment_intent.get("metadata", {})
    if meta.get("type") != "listing_purchase":
        return
    order_id = int(meta.get("order_id", 0))
    if not order_id:
        return

    order = await db.get(Order, order_id)
    if not order or order.status != "pending":
        return

    order.status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    order.stripe_transfer_id = payment_intent.get("transfer", {}).get("id") if isinstance(
        payment_intent.get("transfer"), dict) else None

    # Mark listing as sold if fully purchased
    listing = await db.get(Listing, order.listing_id)
    if listing:
        if order.quantity >= listing.quantity:
            listing.status = "sold"
        else:
            listing.quantity -= order.quantity

    # Audit trail
    db.add(WalletTransaction(
        user_id=order.seller_id,
        type="sale_payout",
        currency="usd",
        amount=order.payout_amount,
        order_id=order.id,
        note=f"Sale payout for order #{order.id} (listing #{order.listing_id})",
    ))

    await db.commit()


async def mark_shipped(db: AsyncSession, order_id: int, seller_id: int, tracking_number: str) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.seller_id != seller_id:
        raise HTTPException(403, "Not your order")
    if order.status != "paid":
        raise HTTPException(400, f"Order status is '{order.status}', expected 'paid'")
    order.status = "shipped"
    order.tracking_number = tracking_number
    order.shipped_at = datetime.now(timezone.utc)
    await db.commit()
    return order


async def mark_completed(db: AsyncSession, order_id: int, buyer_id: int) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.buyer_id != buyer_id:
        raise HTTPException(403, "Not your order")
    if order.status not in ("shipped", "paid"):
        raise HTTPException(400, f"Order status is '{order.status}'")
    order.status = "completed"
    order.completed_at = datetime.now(timezone.utc)

    # Record the sale price as a market price data point so it influences future prices
    listing = await db.get(Listing, order.listing_id)
    if listing and listing.card_id:
        from app.models.price import CardPrice
        db.add(CardPrice(
            card_id=listing.card_id,
            source="tcgplayer",
            price_type="market",
            price_usd=order.price_each,
            recorded_at=datetime.now(timezone.utc),
        ))

    await db.commit()
    return order
