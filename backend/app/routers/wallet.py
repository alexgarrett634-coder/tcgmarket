from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.services.stripe_service import create_wallet_deposit_intent
from app.services.tier_service import get_user_tier

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("")
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(404, "Wallet not found")
    return {
        "prediction_coins": wallet.prediction_coins,
        "real_credits_usd": wallet.real_credits_usd,
        "updated_at": wallet.updated_at.isoformat(),
    }


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    txns = result.scalars().all()
    return [
        {
            "id": t.id,
            "type": t.type,
            "currency": t.currency,
            "amount": t.amount,
            "order_id": t.order_id,
            "note": t.note,
            "created_at": t.created_at.isoformat(),
        }
        for t in txns
    ]


class DepositRequest(BaseModel):
    amount_usd: float


@router.post("/deposit")
async def deposit(
    body: DepositRequest,
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe PaymentIntent for a wallet top-up (Enterprise only)."""
    from app.models.subscription import Subscription
    sub_res = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = sub_res.scalar_one_or_none()
    if not sub:
        raise HTTPException(400, "Subscription not found")

    intent = await create_wallet_deposit_intent(
        current_user.id, body.amount_usd, sub.stripe_customer_id
    )
    return intent


class WithdrawRequest(BaseModel):
    amount_usd: float


@router.post("/withdraw")
async def withdraw(
    body: WithdrawRequest,
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    """Request a payout. (Stub — real implementation needs Stripe Connect.)"""
    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalar_one_or_none()
    if not wallet or wallet.real_credits_usd < body.amount_usd:
        raise HTTPException(400, "Insufficient balance")
    wallet.real_credits_usd -= body.amount_usd
    db.add(WalletTransaction(
        user_id=current_user.id,
        type="withdrawal",
        currency="usd",
        amount=-body.amount_usd,
        note="Manual withdrawal request",
    ))
    await db.commit()
    return {"message": "Withdrawal submitted. Funds will be returned to your card within 5–7 business days."}
