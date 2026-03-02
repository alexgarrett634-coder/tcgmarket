"""APScheduler job functions — each creates its own DB session."""
import logging
import random
from datetime import datetime
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.subscription import Subscription
from app.services.deal_service import scan_ebay_deals, generate_internal_deals
from app.services.alert_service import evaluate_alerts

logger = logging.getLogger("scheduler")


async def job_refresh_prices() -> None:
    """Fetch TCGdex prices for top-watched cards (30 min interval)."""
    async with AsyncSessionLocal() as db:
        try:
            from app.models.card import Card
            from app.models.watchlist import WatchlistItem
            from sqlalchemy import func
            from app.services.price_service import fetch_and_store_card_prices

            result = await db.execute(
                select(Card)
                .join(WatchlistItem, WatchlistItem.card_id == Card.id, isouter=True)
                .group_by(Card.id)
                .order_by(func.count(WatchlistItem.id).desc())
                .limit(200)
            )
            cards = result.scalars().all()
            for card in cards:
                await fetch_and_store_card_prices(db, card, tier="pro")
            await db.commit()
            logger.info("refresh_prices: refreshed %d cards", len(cards))
        except Exception as e:
            logger.error("refresh_prices error: %s", e)


async def job_scan_ebay_deals() -> None:
    """Poll eBay for deals (60s interval)."""
    async with AsyncSessionLocal() as db:
        try:
            count = await scan_ebay_deals(db)
            if count:
                logger.info("scan_ebay_deals: found %d new deals", count)
        except Exception as e:
            logger.error("scan_ebay_deals error: %s", e)


async def job_evaluate_alerts() -> None:
    """Check watchlist thresholds and fire alerts (15 min interval)."""
    async with AsyncSessionLocal() as db:
        try:
            fired = await evaluate_alerts(db)
            if fired:
                logger.info("evaluate_alerts: fired %d alerts", fired)
        except Exception as e:
            logger.error("evaluate_alerts error: %s", e)


async def job_generate_internal_deals() -> None:
    """Scan marketplace listings vs market prices to create internal deals (300s interval)."""
    async with AsyncSessionLocal() as db:
        try:
            count = await generate_internal_deals(db)
            if count:
                logger.info("generate_internal_deals: created %d new deals", count)
        except Exception as e:
            logger.error("generate_internal_deals error: %s", e)


async def job_update_active_listing_prices() -> None:
    """Apply a micro market-movement to cards with active listings (60s interval).

    Simulates live price discovery: each tick nudges the latest known market price
    by a small random delta (±0.5% per minute, Brownian-motion style) so the
    price history charts show realistic intra-day movement.
    """
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import distinct
            from app.models.listing import Listing
            from app.models.card import Card
            from app.models.price import CardPrice

            # Get distinct card IDs that have active listings
            result = await db.execute(
                select(distinct(Listing.card_id))
                .where(Listing.card_id.is_not(None), Listing.status == "active")
            )
            card_ids = [row[0] for row in result.all()]

            if not card_ids:
                return

            now = datetime.utcnow()
            count = 0

            for card_id in card_ids:
                # Get most recent market price
                latest = await db.execute(
                    select(CardPrice)
                    .where(
                        CardPrice.card_id == card_id,
                        CardPrice.source.in_(["tcgplayer", "pricecharting"]),
                        CardPrice.price_type == "market",
                    )
                    .order_by(CardPrice.recorded_at.desc())
                    .limit(1)
                )
                row = latest.scalar_one_or_none()
                if not row:
                    continue

                # Small random walk: ±0.5% per tick
                delta_pct = random.uniform(-0.005, 0.005)
                new_price = round(max(0.01, row.price_usd * (1 + delta_pct)), 2)

                db.add(CardPrice(
                    card_id=card_id,
                    source="tcgplayer",
                    price_type="market",
                    price_usd=new_price,
                    recorded_at=now,
                ))
                count += 1

            await db.commit()
            if count:
                logger.debug("update_active_listing_prices: updated %d cards", count)
        except Exception as e:
            logger.error("update_active_listing_prices error: %s", e)
