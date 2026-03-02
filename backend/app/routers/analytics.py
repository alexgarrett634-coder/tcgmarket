import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.market import PredictionMarket, MarketPosition
from app.models.price import CardPrice
from app.models.card import Card
from app.models.watchlist import WatchlistItem
from app.models.portfolio import PortfolioItem
from app.services.market_service import get_probability

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/market-movers")
async def market_movers(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    """Top markets by volume in the last 24h."""
    result = await db.execute(
        select(PredictionMarket)
        .where(PredictionMarket.status == "open")
        .order_by(PredictionMarket.total_volume.desc())
        .limit(limit)
    )
    markets = result.scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "probability": get_probability(m.pool_yes, m.pool_no),
            "total_volume": m.total_volume,
            "currency": m.currency,
            "trigger_signal": m.trigger_signal,
        }
        for m in markets
    ]


@router.get("/prediction-accuracy")
async def prediction_accuracy(
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    """Leaderboard: users with best win rate on resolved markets."""
    result = await db.execute(
        select(
            MarketPosition.user_id,
            func.count(MarketPosition.id).label("total"),
            func.sum(
                (MarketPosition.payout > 0).cast(db.bind.dialect.name == "sqlite" and "INTEGER" or "INTEGER")
            ).label("wins"),
        )
        .where(MarketPosition.settled == True)
        .group_by(MarketPosition.user_id)
        .order_by(func.count(MarketPosition.id).desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "user_id": row.user_id,
            "total": row.total,
            "wins": row.wins or 0,
            "win_rate": round((row.wins or 0) / row.total * 100, 1) if row.total else 0,
        }
        for row in rows
    ]


@router.get("/price-movers")
async def price_movers(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    """Cards with the biggest price change over the selected period."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(CardPrice.card_id, func.min(CardPrice.price_usd), func.max(CardPrice.price_usd))
        .where(CardPrice.recorded_at >= cutoff, CardPrice.source == "tcgplayer", CardPrice.price_type == "market")
        .group_by(CardPrice.card_id)
        .having(func.min(CardPrice.price_usd) > 0)
        .limit(limit * 5)
    )
    rows = result.all()
    movers = []
    for card_id, min_price, max_price in rows:
        change = (max_price - min_price) / min_price * 100 if min_price else 0
        movers.append({"card_id": card_id, "min_price": min_price, "max_price": max_price, "change_pct": round(change, 2)})
    movers.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return movers[:limit]


@router.get("/export/watchlist")
async def export_watchlist_csv(
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id)
    )
    items = result.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "item_type", "card_id", "product_id", "preferred_source", "alert_above", "alert_below", "notes", "created_at"])
    for i in items:
        writer.writerow([i.id, i.item_type, i.card_id, i.product_id, i.preferred_source, i.alert_above, i.alert_below, i.notes, i.created_at.isoformat()])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=watchlist.csv"},
    )


@router.get("/export/portfolio")
async def export_portfolio_csv(
    current_user: User = Depends(require_tier("enterprise")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PortfolioItem).where(PortfolioItem.user_id == current_user.id)
    )
    items = result.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "item_type", "card_id", "product_id", "quantity", "condition", "purchase_price", "purchase_date", "notes", "created_at"])
    for i in items:
        writer.writerow([i.id, i.item_type, i.card_id, i.product_id, i.quantity, i.condition, i.purchase_price, i.purchase_date, i.notes, i.created_at.isoformat()])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio.csv"},
    )
