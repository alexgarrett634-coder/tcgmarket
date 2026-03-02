from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.card import Card
from app.models.price import CardPrice
from app.services.price_service import fetch_and_store_card_prices

router = APIRouter(prefix="/op", tags=["onepiece"])


_OP_IMG_BASE = "https://en.onepiece-cardgame.com/images/cardlist/card"


def _op_image(number: str | None) -> str | None:
    if not number:
        return None
    return f"{_OP_IMG_BASE}/{number}.png"


def _card_fmt(c: Card) -> dict:
    img = _op_image(c.number)
    return {
        "id": c.id,
        "name": c.name,
        "set_name": c.set_name,
        "set_code": c.set_code,
        "number": c.number,
        "rarity": c.rarity,
        "supertype": c.supertype,
        "image_small": img,
        "image_large": img,
    }


@router.get("/sets")
async def list_op_sets(db: AsyncSession = Depends(get_db)):
    """Return all distinct One Piece set names ordered alphabetically."""
    result = await db.execute(
        select(Card.set_name, func.min(Card.set_code).label("set_code"))
        .where(Card.language == "op")
        .group_by(Card.set_name)
        .order_by(Card.set_name)
    )
    rows = result.all()
    return [{"set_code": r.set_code, "set_name": r.set_name} for r in rows]


@router.get("/search")
async def search_op_cards(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Card)
        .where(
            Card.language == "op",
            or_(Card.name.ilike(f"%{q}%"), Card.set_name.ilike(f"%{q}%")),
        )
        .order_by(Card.name)
        .limit(page_size)
        .offset(offset)
    )
    cards = list(result.scalars().all())
    return {"results": [_card_fmt(c) for c in cards], "page": page, "page_size": page_size}


@router.get("/{card_id}")
async def get_op_card(card_id: str, db: AsyncSession = Depends(get_db)):
    card = await db.get(Card, card_id)
    if not card or card.language != "op":
        raise HTTPException(404, "One Piece card not found")
    return _card_fmt(card)


@router.get("/{card_id}/prices")
async def get_op_card_prices(card_id: str, db: AsyncSession = Depends(get_db)):
    card = await db.get(Card, card_id)
    if not card or card.language != "op":
        raise HTTPException(404, "One Piece card not found")

    prices = await fetch_and_store_card_prices(db, card, tier="pro")
    await db.commit()

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
        "history": [],
        "history_days": 0,
    }
