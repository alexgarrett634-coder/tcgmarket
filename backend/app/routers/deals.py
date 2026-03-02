from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.deal import DealListing, DealAlert
from app.services.deal_service import (
    get_active_deals, subscribe_deals, unsubscribe_deals, deal_event_stream
)

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/top5")
async def top5_deals(db: AsyncSession = Depends(get_db)):
    """Free tier teaser: top 5 best deals only."""
    result = await db.execute(
        select(DealListing)
        .where(DealListing.status == "active")
        .order_by(DealListing.deal_score.desc())
        .limit(5)
    )
    deals = result.scalars().all()
    return [
        {
            "id": d.id,
            "card_id": d.card_id,
            "source": d.source,
            "listed_price": d.listed_price,
            "market_price": d.market_price,
            "deal_score": d.deal_score,
            "condition": d.condition,
            "listing_url": d.listing_url,
        }
        for d in deals
    ]


@router.get("")
async def deals_feed(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    return await get_active_deals(db, limit=limit, offset=offset)


@router.get("/stream")
async def deals_stream(current_user: User | None = Depends(get_current_user_optional)):
    """SSE stream of new deals for Pro+ users."""
    q = subscribe_deals()

    async def generator():
        try:
            async for event in deal_event_stream(q):
                yield event
        finally:
            unsubscribe_deals(q)

    return StreamingResponse(generator(), media_type="text/event-stream")


class DealAlertCreate(BaseModel):
    item_type: str
    card_id: str | None = None
    product_id: int | None = None
    min_deal_score: float = 10.0


@router.post("/alerts", status_code=201)
async def create_deal_alert(
    body: DealAlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = DealAlert(
        user_id=current_user.id,
        item_type=body.item_type,
        card_id=body.card_id,
        product_id=body.product_id,
        min_deal_score=body.min_deal_score,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return {"id": alert.id, "min_deal_score": alert.min_deal_score}


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_deal_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await db.get(DealAlert, alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
    await db.commit()
