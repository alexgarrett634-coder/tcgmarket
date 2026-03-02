from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.tier_guard import require_tier
from app.models.user import User
from app.models.watchlist import WatchlistItem
from app.services.tier_service import get_watchlist_limit, get_user_tier

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistCreate(BaseModel):
    item_type: str
    card_id: str | None = None
    product_id: int | None = None
    preferred_source: str = "tcgplayer"
    alert_above: float | None = None
    alert_below: float | None = None
    alert_enabled: bool = True
    notes: str | None = None


class WatchlistUpdate(BaseModel):
    preferred_source: str | None = None
    alert_above: float | None = None
    alert_below: float | None = None
    alert_enabled: bool | None = None
    notes: str | None = None


@router.get("")
async def list_watchlist(
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .order_by(WatchlistItem.created_at.desc())
    )
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "item_type": i.item_type,
            "card_id": i.card_id,
            "product_id": i.product_id,
            "preferred_source": i.preferred_source,
            "alert_above": i.alert_above,
            "alert_below": i.alert_below,
            "alert_enabled": i.alert_enabled,
            "notes": i.notes,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.post("", status_code=201)
async def add_to_watchlist(
    body: WatchlistCreate,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    tier = await get_user_tier(db, current_user.id)
    limit = get_watchlist_limit(tier)

    count_result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == current_user.id)
    )
    count = len(count_result.scalars().all())
    if count >= limit:
        raise HTTPException(400, f"Watchlist limit of {limit} reached. Upgrade to Enterprise for unlimited.")

    item = WatchlistItem(
        user_id=current_user.id,
        item_type=body.item_type,
        card_id=body.card_id,
        product_id=body.product_id,
        preferred_source=body.preferred_source,
        alert_above=body.alert_above,
        alert_below=body.alert_below,
        alert_enabled=body.alert_enabled,
        notes=body.notes,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}


@router.patch("/{item_id}")
async def update_watchlist_item(
    item_id: int,
    body: WatchlistUpdate,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(WatchlistItem, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(404, "Watchlist item not found")
    if body.preferred_source is not None:
        item.preferred_source = body.preferred_source
    if body.alert_above is not None:
        item.alert_above = body.alert_above
    if body.alert_below is not None:
        item.alert_below = body.alert_below
    if body.alert_enabled is not None:
        item.alert_enabled = body.alert_enabled
    if body.notes is not None:
        item.notes = body.notes
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}", status_code=204)
async def remove_from_watchlist(
    item_id: int,
    current_user: User = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(WatchlistItem, item_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(404, "Watchlist item not found")
    await db.delete(item)
    await db.commit()
