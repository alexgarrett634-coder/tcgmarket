from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notes = result.scalars().all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "link": n.link,
            "seen": n.seen,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]


@router.get("/unseen-count")
async def unseen_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.seen == False,
        )
    )
    count = len(result.scalars().all())
    return {"count": count}


@router.post("/mark-all-seen")
async def mark_all_seen(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.seen == False,
        )
    )
    for n in result.scalars().all():
        n.seen = True
    await db.commit()
    return {"ok": True}


@router.patch("/{notification_id}/seen")
async def mark_seen(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    n = await db.get(Notification, notification_id)
    if n and n.user_id == current_user.id:
        n.seen = True
        await db.commit()
    return {"ok": True}
