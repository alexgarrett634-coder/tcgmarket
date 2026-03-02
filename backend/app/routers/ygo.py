import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.card import Card
from app.models.price import CardPrice
from app.services.price_service import fetch_and_store_card_prices, get_price_history
from app.fetchers.ygoprodeck import fetch_ygo_card_info

router = APIRouter(prefix="/ygo", tags=["ygo"])


def _card_fmt(c: Card, extra: dict | None = None) -> dict:
    extra = extra or {}
    subtypes_parsed: dict = {}
    if c.subtypes and c.subtypes.startswith("{"):
        try:
            subtypes_parsed = json.loads(c.subtypes)
        except Exception:
            pass
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
        # enriched fields from ygoprodeck
        "attribute": extra.get("attribute") or subtypes_parsed.get("attribute"),
        "race": extra.get("race") or subtypes_parsed.get("race"),
        "atk": extra.get("atk") if extra.get("atk") is not None else subtypes_parsed.get("atk"),
        "def": extra.get("def") if extra.get("def") is not None else subtypes_parsed.get("def"),
        "desc": extra.get("desc") or subtypes_parsed.get("desc"),
    }


@router.get("/sets")
async def list_ygo_sets(db: AsyncSession = Depends(get_db)):
    """Return all distinct YGO set names ordered alphabetically."""
    result = await db.execute(
        select(Card.set_name, func.min(Card.set_code).label("set_code"))
        .where(Card.language == "ygo")
        .group_by(Card.set_name)
        .order_by(Card.set_name)
    )
    rows = result.all()
    return [{"set_code": r.set_code, "set_name": r.set_name} for r in rows]


@router.get("/search")
async def search_ygo_cards(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Card)
        .where(
            Card.language == "ygo",
            or_(Card.name.ilike(f"%{q}%"), Card.set_name.ilike(f"%{q}%")),
        )
        .order_by(Card.name)
        .limit(page_size)
        .offset(offset)
    )
    cards = list(result.scalars().all())
    return {"results": [_card_fmt(c) for c in cards], "page": page, "page_size": page_size}


@router.get("/{card_id}")
async def get_ygo_card(card_id: str, db: AsyncSession = Depends(get_db)):
    card = await db.get(Card, card_id)
    if not card or card.language != "ygo":
        raise HTTPException(404, "YGO card not found")

    extra: dict = {}
    if card.image_small is None:
        info = await fetch_ygo_card_info(card.name)
        if info:
            card.image_small = info.get("image_small")
            card.image_large = info.get("image_large")
            if info.get("card_type"):
                card.supertype = info["card_type"]
            card.subtypes = json.dumps({
                "attribute": info.get("attribute"),
                "race": info.get("race"),
                "atk": info.get("atk"),
                "def": info.get("def"),
                "desc": info.get("desc"),
            })
            await db.commit()
            await db.refresh(card)
            extra = info

    return _card_fmt(card, extra)


@router.get("/{card_id}/prices")
async def get_ygo_card_prices(card_id: str, db: AsyncSession = Depends(get_db)):
    card = await db.get(Card, card_id)
    if not card or card.language != "ygo":
        raise HTTPException(404, "YGO card not found")

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
