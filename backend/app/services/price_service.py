import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.card import Card
from app.models.price import CardPrice, ProductPrice, PriceFetchLog
from app.fetchers import tcgdex, ebay, pricecharting
from app.fetchers.base import is_stale, update_fetch_log
from app.services.tier_service import tier_gte


async def fetch_and_store_card_prices(db: AsyncSession, card: Card, tier: str) -> list[CardPrice]:
    sources = []
    if tier_gte(tier, "pro"):
        sources.extend(["ebay", "pricecharting"])

    tasks = []
    for source in sources:
        stale = await is_stale(db, "card", card.id, source, 4.0 if source == "tcgdex" else 6.0)
        if stale:
            tasks.append(_fetch_card_source(db, card, source))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    cutoff_short = datetime.utcnow() - timedelta(hours=24)
    cutoff_long  = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(CardPrice).where(
            CardPrice.card_id == card.id,
            or_(
                and_(CardPrice.source != 'pricecharting', CardPrice.recorded_at >= cutoff_short),
                and_(CardPrice.source == 'pricecharting', CardPrice.recorded_at >= cutoff_long),
            )
        ).order_by(CardPrice.recorded_at.desc())
    )
    return result.scalars().all()


async def _fetch_card_source(db: AsyncSession, card: Card, source: str) -> None:
    try:
        prices = []
        if source == "tcgdex":
            prices = await tcgdex.fetch_card_prices(card.set_code, card.number or "1")
        elif source == "ebay":
            listings = await ebay.search_listings(f"{card.name} {card.set_name} pokemon card", limit=5)
            if listings:
                avg = sum(l["price"] for l in listings) / len(listings)
                prices = [{"source": "ebay", "price_type": "listed", "price_usd": avg}]
        elif source == "pricecharting":
            pass

        for p in prices:
            db.add(CardPrice(
                card_id=card.id,
                source=p["source"],
                price_type=p["price_type"],
                price_usd=p["price_usd"],
            ))
        await update_fetch_log(db, "card", card.id, source, "ok")
    except Exception:
        await update_fetch_log(db, "card", card.id, source, "error")


async def get_price_history(db: AsyncSession, card_id: str, source: str, days: int) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(CardPrice).where(
            CardPrice.card_id == card_id,
            CardPrice.source == source,
            CardPrice.recorded_at >= cutoff,
        ).order_by(CardPrice.recorded_at.asc())
    )
    rows = result.scalars().all()
    return [{"recorded_at": r.recorded_at.isoformat(), "price_usd": r.price_usd, "price_type": r.price_type} for r in rows]


async def get_latest_price(db: AsyncSession, card_id: str, source: str = "tcgplayer") -> float | None:
    result = await db.execute(
        select(CardPrice).where(
            CardPrice.card_id == card_id,
            CardPrice.source == source,
            CardPrice.price_type == "market",
        ).order_by(CardPrice.recorded_at.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    return row.price_usd if row else None
