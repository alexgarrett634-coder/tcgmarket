"""CRUD helpers for Listing and SellerProfile."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.listing import Listing, SellerProfile
from app.models.card import Card
from app.models.product import SealedProduct


def _with_relations(stmt):
    """Eagerly load seller, card, and product to avoid async lazy-loading errors."""
    return stmt.options(
        selectinload(Listing.seller),
        selectinload(Listing.card),
        selectinload(Listing.product),
    )


async def get_seller_profile(db: AsyncSession, user_id: int) -> SellerProfile | None:
    result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def get_or_create_seller_profile(db: AsyncSession, user_id: int) -> SellerProfile:
    profile = await get_seller_profile(db, user_id)
    if not profile:
        profile = SellerProfile(user_id=user_id)
        db.add(profile)
        await db.flush()
    return profile


async def get_listings(
    db: AsyncSession,
    *,
    status: str = "active",
    item_type: str = "",
    card_id: str = "",
    condition: str = "",
    price_min: float | None = None,
    price_max: float | None = None,
    search: str = "",
    set_code: str = "",
    language: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[Listing]:
    stmt = _with_relations(select(Listing).where(Listing.status == status))
    if item_type:
        stmt = stmt.where(Listing.item_type == item_type)
    if card_id:
        stmt = stmt.where(Listing.card_id == card_id)
    if condition:
        stmt = stmt.where(Listing.condition == condition)
    if price_min is not None:
        stmt = stmt.where(Listing.price >= price_min)
    if price_max is not None:
        stmt = stmt.where(Listing.price <= price_max)
    if search:
        stmt = stmt.where(Listing.title.ilike(f"%{search}%"))
    # Card-level filters: join Card when needed
    if set_code or language:
        stmt = stmt.join(Card, Listing.card_id == Card.id)
        if set_code:
            stmt = stmt.where(Card.set_code == set_code)
        if language:
            stmt = stmt.where(Card.language == language)
    stmt = stmt.order_by(Listing.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_listing_by_id(db: AsyncSession, listing_id: int) -> Listing | None:
    result = await db.execute(
        _with_relations(select(Listing).where(Listing.id == listing_id))
    )
    return result.scalar_one_or_none()


async def get_listings_by_seller(db: AsyncSession, seller_id: int, status: str = "") -> list[Listing]:
    stmt = _with_relations(select(Listing).where(Listing.seller_id == seller_id))
    if status:
        stmt = stmt.where(Listing.status == status)
    stmt = stmt.order_by(Listing.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_listing(db: AsyncSession, seller_id: int, data: dict) -> Listing:
    """Create a listing and return it with relationships loaded."""
    if data.get("item_type") == "card":
        card = await db.get(Card, data["card_id"])
        if not card:
            raise HTTPException(404, "Card not found")
        title = data.get("title") or f"{card.name} ({data['condition']})"
        listing = Listing(
            seller_id=seller_id,
            item_type="card",
            card_id=data["card_id"],
            title=title,
            description=data.get("description"),
            condition=data["condition"],
            quantity=data.get("quantity", 1),
            price=data["price"],
            grade=data.get("grade"),
            grading_company=data.get("grading_company"),
        )
    else:
        product = await db.get(SealedProduct, data["product_id"])
        if not product:
            raise HTTPException(404, "Product not found")
        title = data.get("title") or f"{product.name} ({data['condition']})"
        listing = Listing(
            seller_id=seller_id,
            item_type="sealed",
            product_id=data["product_id"],
            title=title,
            description=data.get("description"),
            condition=data["condition"],
            quantity=data.get("quantity", 1),
            price=data["price"],
            grade=data.get("grade"),
            grading_company=data.get("grading_company"),
        )
    db.add(listing)
    await db.flush()
    return listing


async def cancel_listing(db: AsyncSession, listing_id: int, seller_id: int) -> Listing:
    listing = await get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.seller_id != seller_id:
        raise HTTPException(403, "Not your listing")
    if listing.status != "active":
        raise HTTPException(400, f"Cannot cancel a listing with status '{listing.status}'")
    listing.status = "cancelled"
    return listing


async def get_seller_stats(db: AsyncSession, user_id: int) -> dict:
    from app.models.order import Order
    active = await db.execute(
        select(func.count(Listing.id)).where(Listing.seller_id == user_id, Listing.status == "active")
    )
    sold = await db.execute(
        select(func.count(Listing.id)).where(Listing.seller_id == user_id, Listing.status == "sold")
    )
    earnings = await db.execute(
        select(func.coalesce(func.sum(Order.payout_amount), 0)).where(
            Order.seller_id == user_id, Order.status.in_(["paid", "shipped", "completed"])
        )
    )
    return {
        "active_listings": active.scalar() or 0,
        "sold_listings": sold.scalar() or 0,
        "total_earnings": float(earnings.scalar() or 0),
    }
