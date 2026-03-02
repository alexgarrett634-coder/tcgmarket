"""eBay deal scanning, scoring, SSE broadcasting, and internal deal generation."""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.card import Card
from app.models.deal import DealListing, DealAlert
from app.models.notification import Notification
from app.models.watchlist import WatchlistItem
from app.models.listing import Listing
from app.fetchers import ebay
from app.services.price_service import get_latest_price

# In-process SSE queues: list of asyncio.Queue objects (one per connected Pro+ client)
_deal_queues: list[asyncio.Queue] = []


def subscribe_deals() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _deal_queues.append(q)
    return q


def unsubscribe_deals(q: asyncio.Queue) -> None:
    try:
        _deal_queues.remove(q)
    except ValueError:
        pass


async def _broadcast_deal(deal: DealListing) -> None:
    payload = json.dumps({
        "id": deal.id,
        "item_type": deal.item_type,
        "card_id": deal.card_id,
        "source": deal.source,
        "listing_url": deal.listing_url,
        "listed_price": deal.listed_price,
        "market_price": deal.market_price,
        "deal_score": deal.deal_score,
        "condition": deal.condition,
        "seller": deal.seller,
        "discovered_at": deal.discovered_at.isoformat(),
    })
    for q in list(_deal_queues):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def deal_event_stream(q: asyncio.Queue) -> AsyncIterator[str]:
    """Yields SSE-formatted strings."""
    try:
        while True:
            data = await asyncio.wait_for(q.get(), timeout=30.0)
            yield f"data: {data}\n\n"
    except asyncio.TimeoutError:
        yield ": keepalive\n\n"
    except asyncio.CancelledError:
        return


async def scan_ebay_deals(db: AsyncSession) -> int:
    """
    Poll eBay for the top watched cards, compare against market price,
    store new deals, broadcast via SSE. Returns count of new deals found.
    """
    # Gather top-watched cards (up to 500)
    result = await db.execute(
        select(Card)
        .join(WatchlistItem, WatchlistItem.card_id == Card.id, isouter=True)
        .group_by(Card.id)
        .order_by(Card.id)
        .limit(500)
    )
    cards = result.scalars().all()

    new_deals = 0
    for card in cards:
        market_price = await get_latest_price(db, card.id, source="tcgplayer")
        if not market_price or market_price <= 0:
            continue

        query = f"{card.name} {card.set_name} pokemon card"
        listings = await ebay.search_listings(query, limit=5)

        for listing in listings:
            listed = listing["price"]
            if listed <= 0:
                continue
            score = (market_price - listed) / market_price * 100
            if score < 10.0:
                continue

            expires = datetime.now(timezone.utc) + timedelta(hours=48)
            # Upsert by (source, external_id)
            existing = await db.execute(
                select(DealListing).where(
                    DealListing.source == "ebay",
                    DealListing.external_id == listing["external_id"],
                )
            )
            deal = existing.scalar_one_or_none()
            if deal:
                deal.listed_price = listed
                deal.market_price = market_price
                deal.deal_score = round(score, 2)
                deal.expires_at = expires
                deal.status = "active"
            else:
                deal = DealListing(
                    item_type="card",
                    card_id=card.id,
                    source="ebay",
                    external_id=listing["external_id"],
                    listing_url=listing["url"],
                    listed_price=listed,
                    market_price=market_price,
                    deal_score=round(score, 2),
                    condition=listing.get("condition", ""),
                    seller=listing.get("seller", ""),
                    expires_at=expires,
                )
                db.add(deal)
                new_deals += 1
                await db.flush()
                await _broadcast_deal(deal)

    # Mark expired deals
    await db.execute(
        select(DealListing).where(
            DealListing.expires_at < datetime.now(timezone.utc),
            DealListing.status == "active",
        )
    )
    # (bulk update via ORM loop is fine for SQLite scale)
    expired_res = await db.execute(
        select(DealListing).where(
            DealListing.expires_at < datetime.now(timezone.utc),
            DealListing.status == "active",
        )
    )
    for d in expired_res.scalars().all():
        d.status = "expired"

    await db.commit()
    return new_deals


async def get_active_deals(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[dict]:
    result = await db.execute(
        select(DealListing)
        .options(selectinload(DealListing.card))
        .where(DealListing.status == "active")
        .order_by(DealListing.deal_score.desc())
        .limit(limit)
        .offset(offset)
    )
    deals = result.scalars().all()
    return [
        {
            "id": d.id,
            "item_type": d.item_type,
            "card_id": d.card_id,
            "card_name": d.card.name if d.card else d.card_id,
            "card_image": d.card.image_small if d.card else None,
            "source": d.source,
            "listing_url": d.listing_url,
            "listed_price": d.listed_price,
            "market_price": d.market_price,
            "deal_score": d.deal_score,
            "condition": d.condition,
            "seller": d.seller,
            "discovered_at": d.discovered_at.isoformat(),
        }
        for d in deals
    ]


async def generate_internal_deals(db: AsyncSession) -> int:
    """
    Compare marketplace listing prices vs market prices.
    Listings priced 10%+ below market become internal deals.
    """
    from app.models.price import CardPrice

    # Get all active card listings
    result = await db.execute(
        select(Listing)
        .where(Listing.status == "active", Listing.card_id.is_not(None))
        .options(selectinload(Listing.card))
    )
    listings = result.scalars().all()

    new_deals = 0
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=48)

    for listing in listings:
        market_price = await get_latest_price(db, listing.card_id, source="tcgplayer")
        if not market_price or market_price <= 0:
            # Fall back to heuristic price
            market_price = await get_latest_price(db, listing.card_id, source="heuristic")
        if not market_price or market_price <= 0:
            continue

        score = (market_price - listing.price) / market_price * 100
        if score < 8.0:
            continue

        external_id = f"internal-{listing.id}"
        existing = await db.execute(
            select(DealListing).where(
                DealListing.source == "internal",
                DealListing.external_id == external_id,
            )
        )
        deal = existing.scalar_one_or_none()
        if deal:
            deal.listed_price = listing.price
            deal.market_price = market_price
            deal.deal_score = round(score, 2)
            deal.expires_at = expires
            deal.status = "active"
        else:
            deal = DealListing(
                item_type="card",
                card_id=listing.card_id,
                source="internal",
                external_id=external_id,
                listing_url=f"/marketplace/{listing.id}",
                listed_price=listing.price,
                market_price=market_price,
                deal_score=round(score, 2),
                condition=listing.condition,
                seller="",
                expires_at=expires,
            )
            db.add(deal)
            new_deals += 1

    # Expire deals whose listing is no longer active
    active_external_ids = {f"internal-{l.id}" for l in listings}
    expired_res = await db.execute(
        select(DealListing).where(
            DealListing.source == "internal",
            DealListing.status == "active",
        )
    )
    for d in expired_res.scalars().all():
        if d.external_id not in active_external_ids:
            d.status = "expired"

    await db.commit()
    return new_deals


async def notify_deal_alert_users(db: AsyncSession, deal: DealListing) -> None:
    """Check saved deal alerts and notify matching users."""
    result = await db.execute(
        select(DealAlert).where(
            DealAlert.min_deal_score <= deal.deal_score,
        )
    )
    alerts = result.scalars().all()
    for alert in alerts:
        if alert.card_id and alert.card_id != deal.card_id:
            continue
        if alert.product_id and alert.product_id != deal.product_id:
            continue
        db.add(Notification(
            user_id=alert.user_id,
            type="deal_alert",
            title="Deal Alert!",
            message=f"A {deal.deal_score:.0f}% deal was found on {deal.source}.",
            link=deal.listing_url,
        ))
