"""Auto-generation of prediction markets based on price signals."""
import statistics
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.card import Card
from app.models.market import PredictionMarket
from app.models.price import CardPrice
from app.models.watchlist import WatchlistItem
from app.config import settings


async def get_most_watched_cards(db: AsyncSession, limit: int = 100) -> list[Card]:
    """Return cards ordered by watchlist count."""
    result = await db.execute(
        select(Card)
        .join(WatchlistItem, WatchlistItem.card_id == Card.id, isouter=True)
        .group_by(Card.id)
        .order_by(func.count(WatchlistItem.id).desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_price_series(db: AsyncSession, card_id: str, days: int = 30) -> list[float]:
    """Return list of price_usd values (market, tcgplayer) oldest → newest."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(CardPrice.price_usd).where(
            CardPrice.card_id == card_id,
            CardPrice.source == "tcgplayer",
            CardPrice.price_type == "market",
            CardPrice.recorded_at >= cutoff,
        ).order_by(CardPrice.recorded_at.asc())
    )
    return [row[0] for row in result.all()]


async def has_open_market(db: AsyncSession, card_id: str | None, product_id: int | None) -> bool:
    """True if there is already an open market for this item."""
    q = select(PredictionMarket).where(PredictionMarket.status == "open")
    if card_id:
        q = q.where(PredictionMarket.card_id == card_id)
    if product_id:
        q = q.where(PredictionMarket.product_id == product_id)
    result = await db.execute(q)
    return result.scalar_one_or_none() is not None


async def maybe_create_market(
    db: AsyncSession,
    card: Card,
    market_type: str,
    target: float,
    days: int,
    trigger_signal: str,
) -> PredictionMarket | None:
    """Create a market only if no open market exists for this card."""
    if await has_open_market(db, card.id, None):
        return None

    target_date = datetime.now(timezone.utc) + timedelta(days=days)
    pool = float(settings.market_initial_pool)

    if market_type == "price_above":
        title = f"Will {card.name} stay above ${target:.2f} in {days} days?"
    elif market_type == "price_recover":
        title = f"Will {card.name} recover above ${target:.2f} in {days} days?"
    elif market_type == "new_high":
        title = f"Will {card.name} reach a new 30-day high in the next {days * 24} hours?"
    elif market_type == "stagnant_move":
        title = f"Will {card.name} move more than 15% in either direction this month?"
    else:
        title = f"Will {card.name} hit ${target:.2f} in {days} days?"

    market = PredictionMarket(
        title=title,
        item_type="card",
        card_id=card.id,
        market_type=market_type,
        currency="coins",
        target_value=target,
        target_date=target_date,
        pool_yes=pool,
        pool_no=pool,
        trigger_signal=trigger_signal,
    )
    db.add(market)
    await db.flush()
    return market


async def generate_markets(db: AsyncSession) -> int:
    """
    Standard 30-min market generation pass.
    Returns count of markets created.
    """
    created = 0
    cards = await get_most_watched_cards(db, limit=100)

    for card in cards:
        prices = await get_price_series(db, card.id, days=30)
        if len(prices) < 7:
            continue

        mean = statistics.mean(prices)
        stdev = statistics.stdev(prices)
        current = prices[-1]

        if current > mean + 2 * stdev:
            m = await maybe_create_market(
                db, card, "price_above",
                target=round(current * 0.95, 2),
                days=7,
                trigger_signal="price_spike",
            )
            if m:
                created += 1
        elif current < mean - 2 * stdev:
            m = await maybe_create_market(
                db, card, "price_recover",
                target=round(mean, 2),
                days=7,
                trigger_signal="price_crash",
            )
            if m:
                created += 1

        # Volume-spike check: compare last day vs 7-day avg
        recent = await get_price_series(db, card.id, days=7)
        if len(recent) >= 4:
            avg_vol = statistics.mean(recent[:-1]) if len(recent) > 1 else 0
            if avg_vol > 0 and recent[-1] > avg_vol * 3:
                m = await maybe_create_market(
                    db, card, "new_high",
                    target=round(max(prices), 2),
                    days=3,
                    trigger_signal="volume_spike",
                )
                if m:
                    created += 1

        # Stagnant: if std dev is tiny relative to mean
        if mean > 0 and (stdev / mean) < 0.05 and len(prices) >= 30:
            m = await maybe_create_market(
                db, card, "stagnant_move",
                target=round(mean * 1.15, 2),
                days=30,
                trigger_signal="stagnant",
            )
            if m:
                created += 1

    await db.commit()
    return created


async def check_volatility(db: AsyncSession) -> int:
    """
    60-second emergency check: only reacts to extreme single-candle moves.
    Returns count of emergency markets created.
    """
    created = 0
    cards = await get_most_watched_cards(db, limit=50)

    for card in cards:
        prices = await get_price_series(db, card.id, days=2)
        if len(prices) < 2:
            continue
        prev, current = prices[-2], prices[-1]
        if prev == 0:
            continue
        change = abs(current - prev) / prev
        if change >= 0.20:  # 20%+ move in one interval = emergency
            signal = "emergency_spike" if current > prev else "emergency_crash"
            target = current if current > prev else prev
            m = await maybe_create_market(
                db, card, "price_above",
                target=round(target * 0.9, 2),
                days=1,
                trigger_signal=signal,
            )
            if m:
                created += 1

    if created:
        await db.commit()
    return created
