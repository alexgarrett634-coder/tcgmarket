from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct

from app.database import get_db
from app.middleware.auth import get_current_user_optional
from app.models.user import User
from app.models.card import Card
from app.fetchers import pokemontcg
from app.services.price_service import fetch_and_store_card_prices, get_price_history

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/sets")
async def list_sets(
    language: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    """Return all distinct sets for a given language, ordered by set name."""
    result = await db.execute(
        select(Card.set_code, Card.set_name)
        .where(Card.language == language)
        .distinct()
        .order_by(Card.set_name)
    )
    rows = result.all()
    return [{"set_code": r.set_code, "set_name": r.set_name} for r in rows]


def _card_fmt(c: Card) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "set_name": c.set_name,
        "set_code": c.set_code,
        "number": c.number,
        "rarity": c.rarity,
        "supertype": c.supertype,
        "subtypes": c.subtypes,
        "image_small": c.image_small,
        "image_large": c.image_large,
    }


@router.get("/search")
async def search_cards(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    # Search local DB first (covers all seeded/imported cards)
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Card)
        .where(Card.name.ilike(f"%{q}%"))
        .order_by(Card.name)
        .limit(page_size)
        .offset(offset)
    )
    local_cards = list(result.scalars().all())

    if local_cards:
        return {"results": [_card_fmt(c) for c in local_cards], "page": page, "page_size": page_size}

    # Fall back to external API if nothing in DB
    cards = await pokemontcg.search_cards(q, page=page, page_size=page_size)
    # Upsert any results into local DB for next time
    for card_data in cards:
        await pokemontcg.upsert_card(db, card_data)
    if cards:
        await db.commit()

    return {"results": cards, "page": page, "page_size": page_size}


@router.get("/{card_id}")
async def get_card(card_id: str, db: AsyncSession = Depends(get_db)):
    local = await db.get(Card, card_id)
    if not local:
        data = await pokemontcg.get_card(card_id)
        if not data:
            raise HTTPException(404, "Card not found")
        await pokemontcg.upsert_card(db, data)
        await db.commit()
        local = await db.get(Card, card_id)
    return _card_fmt(local)


@router.get("/{card_id}/prices")
async def get_card_prices(
    card_id: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    card = await db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Card not found")

    tier = "pro"  # All users get full price history now
    prices = await fetch_and_store_card_prices(db, card, tier)
    await db.commit()

    history = await get_price_history(db, card_id, source="tcgplayer", days=90)

    return {
        "current": [
            {
                "source": p.source,
                "price_type": p.price_type,
                "price_usd": p.price_usd,
                "recorded_at": p.recorded_at.isoformat(),
            }
            for p in prices
        ],
        "history": history,
        "history_days": 90,
    }
