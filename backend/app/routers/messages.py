"""Listing messages: buyer ↔ seller direct messaging per listing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.message import ListingMessage

router = APIRouter(prefix="/listings", tags=["messages"])


def _fmt(msg: ListingMessage) -> dict:
    return {
        "id": msg.id,
        "listing_id": msg.listing_id,
        "sender_id": msg.sender_id,
        "sender_email": msg.sender.email if msg.sender else None,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "seen": msg.seen,
        "created_at": msg.created_at.isoformat(),
    }


@router.get("/{listing_id}/messages")
async def get_messages(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages on a listing thread where current user is sender or receiver."""
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")

    result = await db.execute(
        select(ListingMessage)
        .options(selectinload(ListingMessage.sender), selectinload(ListingMessage.receiver))
        .where(
            ListingMessage.listing_id == listing_id,
            or_(
                ListingMessage.sender_id == current_user.id,
                ListingMessage.receiver_id == current_user.id,
            )
        )
        .order_by(ListingMessage.created_at.asc())
    )
    messages = result.scalars().all()

    # Mark received messages as seen
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.seen:
            msg.seen = True
    await db.commit()

    return [_fmt(m) for m in messages]


class SendMessageRequest(BaseModel):
    content: str


@router.post("/{listing_id}/messages", status_code=201)
async def send_message(
    listing_id: int,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message about a listing. Buyers message seller; sellers reply to buyers."""
    if not body.content.strip():
        raise HTTPException(400, "Message cannot be empty")

    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")

    # Determine receiver: if sender is seller → need buyer context (reply to latest message)
    # If sender is buyer → receiver is seller
    if current_user.id == listing.seller_id:
        # Seller replying — find the most recent message from a buyer to reply to
        result = await db.execute(
            select(ListingMessage)
            .where(
                ListingMessage.listing_id == listing_id,
                ListingMessage.receiver_id == listing.seller_id,
            )
            .order_by(ListingMessage.created_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if not latest:
            raise HTTPException(400, "No buyer has messaged about this listing yet")
        receiver_id = latest.sender_id
    else:
        receiver_id = listing.seller_id

    if current_user.id == receiver_id:
        raise HTTPException(400, "Cannot message yourself")

    msg = ListingMessage(
        listing_id=listing_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=body.content.strip(),
    )
    db.add(msg)
    await db.commit()
    # Re-fetch with relationships loaded
    result = await db.execute(
        select(ListingMessage)
        .options(selectinload(ListingMessage.sender), selectinload(ListingMessage.receiver))
        .where(ListingMessage.id == msg.id)
    )
    msg = result.scalar_one()
    return _fmt(msg)
