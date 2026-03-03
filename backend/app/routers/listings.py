from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete as sql_delete
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.listing import Listing
from app.services import listing_service

router = APIRouter(prefix="/listings", tags=["listings"])


def _fmt(listing: Listing) -> dict:
    seller = listing.seller
    card = listing.card
    product = listing.product
    return {
        "id": listing.id,
        "seller_id": listing.seller_id,
        "seller_email": seller.email if seller else None,
        "item_type": listing.item_type,
        "card_id": listing.card_id,
        "card": {
            "id": card.id,
            "name": card.name,
            "set_name": card.set_name,
            "rarity": card.rarity,
            "image_small": card.image_small,
            "image_large": card.image_large,
        } if card else None,
        "product_id": listing.product_id,
        "product": {
            "id": product.id,
            "name": product.name,
            "set_name": product.set_name,
            "product_type": product.product_type,
            "image_url": product.image_url,
        } if product else None,
        "title": listing.title,
        "description": listing.description,
        "condition": listing.condition,
        "quantity": listing.quantity,
        "price": listing.price,
        "status": listing.status,
        "grade": listing.grade,
        "grading_company": listing.grading_company,
        "created_at": listing.created_at.isoformat(),
    }


@router.delete("/admin/clear-listings")
async def clear_all_listings(db: AsyncSession = Depends(get_db)):
    """TEMPORARY: Delete all listings. Remove this endpoint after use."""
    await db.execute(sql_delete(Listing))
    await db.commit()
    return {"deleted": "all listings"}


@router.get("")
async def list_listings(
    status: str = Query("active"),
    item_type: str = Query(""),
    card_id: str = Query(""),
    condition: str = Query(""),
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    search: str = Query(""),
    set_code: str = Query(""),
    language: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    listings = await listing_service.get_listings(
        db,
        status=status,
        item_type=item_type,
        card_id=card_id,
        condition=condition,
        price_min=price_min,
        price_max=price_max,
        search=search,
        set_code=set_code,
        language=language,
        limit=limit,
        offset=offset,
    )
    return [_fmt(l) for l in listings]


@router.get("/mine")
async def my_listings(
    status: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listings = await listing_service.get_listings_by_seller(db, current_user.id, status=status)
    return [_fmt(l) for l in listings]


@router.get("/{listing_id}")
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    listing = await listing_service.get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return _fmt(listing)


class CreateListingRequest(BaseModel):
    item_type: str  # 'card' or 'sealed'
    card_id: Optional[str] = None
    product_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    condition: str  # NM, LP, MP, HP, DMG
    quantity: int = 1
    price: float
    grade: Optional[int] = None          # PSA/BGS grade 6–10; omit for raw
    grading_company: Optional[str] = None  # 'PSA', 'BGS', etc.


@router.post("", status_code=201)
async def create_listing(
    body: CreateListingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check seller profile exists and onboarding is complete
    profile = await listing_service.get_seller_profile(db, current_user.id)
    if not profile or not profile.onboarding_complete:
        raise HTTPException(
            400,
            detail={
                "error": "seller_onboarding_required",
                "message": "Complete seller onboarding before creating listings.",
            },
        )
    if body.price <= 0:
        raise HTTPException(400, "Price must be greater than 0")
    if body.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1")
    if body.item_type not in ("card", "sealed"):
        raise HTTPException(400, "item_type must be 'card' or 'sealed'")
    if body.item_type == "card" and not body.card_id:
        raise HTTPException(400, "card_id required for card listings")
    if body.item_type == "sealed" and not body.product_id:
        raise HTTPException(400, "product_id required for sealed listings")

    listing = await listing_service.create_listing(db, current_user.id, body.model_dump())
    await db.commit()
    listing = await listing_service.get_listing_by_id(db, listing.id)
    return _fmt(listing)


class UpdateListingRequest(BaseModel):
    price: Optional[float] = None
    quantity: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None  # only 'cancelled' allowed via this endpoint


@router.patch("/{listing_id}")
async def update_listing(
    listing_id: int,
    body: UpdateListingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await listing_service.get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.seller_id != current_user.id:
        raise HTTPException(403, "Not your listing")
    if listing.status != "active":
        raise HTTPException(400, f"Cannot edit a listing with status '{listing.status}'")

    if body.status == "cancelled":
        listing.status = "cancelled"
    if body.price is not None:
        if body.price <= 0:
            raise HTTPException(400, "Price must be greater than 0")
        listing.price = body.price
    if body.quantity is not None:
        if body.quantity < 1:
            raise HTTPException(400, "Quantity must be at least 1")
        listing.quantity = body.quantity
    if body.description is not None:
        listing.description = body.description

    await db.commit()
    listing = await listing_service.get_listing_by_id(db, listing.id)
    return _fmt(listing)
