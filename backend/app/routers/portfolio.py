from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.portfolio import PortfolioItem
from app.services.price_service import get_latest_price

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PortfolioCreate(BaseModel):
    item_type: str
    card_id: str | None = None
    product_id: int | None = None
    quantity: int = 1
    condition: str = "NM"
    purchase_price: float | None = None
    purchase_date: date | None = None
    preferred_source: str = "tcgplayer"
    notes: str | None = None


class PortfolioUpdate(BaseModel):
    quantity: int | None = None
    condition: str | None = None
    purchase_price: float | None = None
    notes: str | None = None


@router.get("")
async def list_portfolio(
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.user_id == current_user.id)
        .order_by(PortfolioItem.created_at.desc())
    )
    items = result.scalars().all()

    enriched = []
    total_cost = 0.0
    total_value = 0.0

    for item in items:
        current_price = None
        if item.item_type == "card" and item.card_id:
            current_price = await get_latest_price(db, item.card_id, source=item.preferred_source or "tcgplayer")

        cost = (item.purchase_price or 0) * item.quantity
        value = (current_price or 0) * item.quantity
        total_cost += cost
        total_value += value

        enriched.append({
            "id": item.id,
            "item_type": item.item_type,
            "card_id": item.card_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "condition": item.condition,
            "purchase_price": item.purchase_price,
            "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
            "current_price": current_price,
            "total_cost": cost,
            "total_value": value,
            "pnl": value - cost,
            "pnl_pct": ((value - cost) / cost * 100) if cost > 0 else None,
            "notes": item.notes,
            "created_at": item.created_at.isoformat(),
        })

    return {
        "items": enriched,
        "summary": {
            "total_cost": total_cost,
            "total_value": total_value,
            "total_pnl": total_value - total_cost,
            "total_pnl_pct": ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else None,
        },
    }


@router.post("", status_code=201)
async def add_portfolio_item(
    body: PortfolioCreate,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    item = PortfolioItem(
        user_id=current_user.id,
        item_type=body.item_type,
        card_id=body.card_id,
        product_id=body.product_id,
        quantity=body.quantity,
        condition=body.condition,
        purchase_price=body.purchase_price,
        purchase_date=body.purchase_date,
        preferred_source=body.preferred_source,
        notes=body.notes,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}


@router.patch("/{item_id}")
async def update_portfolio_item(
    item_id: int,
    body: PortfolioUpdate,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(PortfolioItem, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(404, "Portfolio item not found")
    if body.quantity is not None:
        item.quantity = body.quantity
    if body.condition is not None:
        item.condition = body.condition
    if body.purchase_price is not None:
        item.purchase_price = body.purchase_price
    if body.notes is not None:
        item.notes = body.notes
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}", status_code=204)
async def delete_portfolio_item(
    item_id: int,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(PortfolioItem, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(404, "Portfolio item not found")
    await db.delete(item)
    await db.commit()
