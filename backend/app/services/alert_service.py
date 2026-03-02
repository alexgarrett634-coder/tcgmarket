"""Evaluate watchlist price alerts and send email + in-app notifications."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.watchlist import WatchlistItem, PriceAlert
from app.models.notification import Notification
from app.services.price_service import get_latest_price


async def evaluate_alerts(db: AsyncSession) -> int:
    """
    Check all enabled watchlist items with price thresholds.
    Fires at most once per 24h per direction per item.
    Returns count of alerts fired.
    """
    fired = 0
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.alert_enabled == True)
    )
    items = result.scalars().all()

    cooldown = datetime.now(timezone.utc) - timedelta(hours=24)

    for item in items:
        if item.item_type == "card" and item.card_id:
            current = await get_latest_price(db, item.card_id, source=item.preferred_source or "tcgplayer")
        else:
            continue  # products not yet implemented

        if current is None:
            continue

        for direction, threshold in [("above", item.alert_above), ("below", item.alert_below)]:
            if threshold is None:
                continue

            triggered = (
                (direction == "above" and current >= threshold) or
                (direction == "below" and current <= threshold)
            )
            if not triggered:
                continue

            # Check cooldown: skip if we already fired this direction in last 24h
            recent = await db.execute(
                select(PriceAlert).where(
                    PriceAlert.watchlist_id == item.id,
                    PriceAlert.direction == direction,
                    PriceAlert.triggered_at >= cooldown,
                )
            )
            if recent.scalar_one_or_none():
                continue

            # Record alert
            alert = PriceAlert(
                watchlist_id=item.id,
                direction=direction,
                triggered_price=current,
                threshold_price=threshold,
            )
            db.add(alert)

            # In-app notification
            label = "above" if direction == "above" else "below"
            db.add(Notification(
                user_id=item.user_id,
                type="price_alert",
                title=f"Price Alert: {label} ${threshold:.2f}",
                message=f"Price is now ${current:.2f} ({label} your ${threshold:.2f} alert).",
                link=f"/prices/{item.card_id}" if item.card_id else None,
            ))

            fired += 1

    await db.commit()
    return fired
