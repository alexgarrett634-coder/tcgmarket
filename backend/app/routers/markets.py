import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_optional
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.market import PredictionMarket, MarketPosition
from app.services.market_service import place_position, get_market_detail, get_probability
from app.services.tier_service import get_user_tier

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("")
async def list_markets(
    currency: str = Query("", description="Filter by 'coins' or 'usd'"),
    status: str = Query("open"),
    item_type: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PredictionMarket).where(PredictionMarket.status == status)
    if currency:
        stmt = stmt.where(PredictionMarket.currency == currency)
    if item_type:
        stmt = stmt.where(PredictionMarket.item_type == item_type)
    stmt = stmt.order_by(PredictionMarket.total_volume.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    markets = result.scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "item_type": m.item_type,
            "card_id": m.card_id,
            "product_id": m.product_id,
            "market_type": m.market_type,
            "currency": m.currency,
            "probability": get_probability(m.pool_yes, m.pool_no),
            "total_volume": m.total_volume,
            "target_date": m.target_date.isoformat(),
            "status": m.status,
            "trigger_signal": m.trigger_signal,
            "created_at": m.created_at.isoformat(),
        }
        for m in markets
    ]


@router.get("/stream")
async def markets_stream(db: AsyncSession = Depends(get_db)):
    """SSE endpoint pushing probability updates every 5 seconds."""
    async def event_generator():
        while True:
            try:
                result = await db.execute(
                    select(PredictionMarket)
                    .where(PredictionMarket.status == "open")
                    .order_by(PredictionMarket.total_volume.desc())
                    .limit(100)
                )
                markets = result.scalars().all()
                payload = json.dumps([
                    {
                        "id": m.id,
                        "probability": get_probability(m.pool_yes, m.pool_no),
                        "total_volume": m.total_volume,
                    }
                    for m in markets
                ])
                yield f"data: {payload}\n\n"
            except Exception:
                yield ": keepalive\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{market_id}")
async def get_market(market_id: int, db: AsyncSession = Depends(get_db)):
    return await get_market_detail(db, market_id)


@router.get("/{market_id}/positions")
async def get_positions(
    market_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MarketPosition).where(
            MarketPosition.market_id == market_id,
            MarketPosition.user_id == current_user.id,
        ).order_by(MarketPosition.created_at.desc())
    )
    positions = result.scalars().all()
    return [
        {
            "id": p.id,
            "side": p.side,
            "shares": p.shares,
            "cost": p.cost,
            "currency": p.currency,
            "settled": p.settled,
            "payout": p.payout,
            "created_at": p.created_at.isoformat(),
        }
        for p in positions
    ]


class BuyRequest(BaseModel):
    side: str  # "yes" or "no"
    amount: float


@router.post("/{market_id}/buy")
async def buy_position(
    market_id: int,
    body: BuyRequest,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    # Extra check: real-money markets require enterprise
    market = await db.get(PredictionMarket, market_id)
    if market and market.currency == "usd":
        tier = await get_user_tier(db, current_user.id)
        if tier != "enterprise":
            raise HTTPException(403, detail={
                "error": "upgrade_required",
                "required_tier": "enterprise",
                "message": "Real-money markets require Enterprise tier",
            })
        # KYC check
        from app.models.wallet import KycVerification
        from sqlalchemy import select as sa_select
        kyc_res = await db.execute(sa_select(KycVerification).where(KycVerification.user_id == current_user.id))
        kyc = kyc_res.scalar_one_or_none()
        if not kyc or kyc.status != "verified":
            raise HTTPException(403, detail={
                "error": "kyc_required",
                "message": "KYC verification is required for real-money markets.",
            })

    result = await place_position(db, current_user.id, market_id, body.side, body.amount)
    await db.commit()
    return result
