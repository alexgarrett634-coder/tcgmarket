from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.listing import SellerProfile
from app.services import listing_service
from app.services.stripe_service import create_seller_account, get_seller_dashboard_link
from app.config import settings

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("/onboard")
async def onboard_seller(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or resume Stripe Connect Express onboarding."""
    profile = await listing_service.get_or_create_seller_profile(db, current_user.id)

    return_url = f"{settings.frontend_url}/seller/dashboard?onboarded=1"
    refresh_url = f"{settings.frontend_url}/seller/dashboard?refresh=1"

    if not settings.stripe_secret_key:
        # Dev mode: mark onboarding complete without Stripe
        profile.stripe_account_id = f"acct_test_{current_user.id}"
        profile.onboarding_complete = True
        await db.commit()
        return {
            "onboarding_url": None,
            "test_mode": True,
            "message": "Stripe not configured — seller account activated in test mode",
            "onboarding_complete": True,
        }

    result = await create_seller_account(current_user.id, return_url, refresh_url)
    profile.stripe_account_id = result["stripe_account_id"]
    await db.commit()
    return {"onboarding_url": result["onboarding_url"], "onboarding_complete": False}


@router.get("/me")
async def get_my_seller_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await listing_service.get_seller_profile(db, current_user.id)
    stats = await listing_service.get_seller_stats(db, current_user.id)
    return {
        "is_seller": profile is not None and profile.onboarding_complete,
        "onboarding_complete": profile.onboarding_complete if profile else False,
        "stripe_account_id": profile.stripe_account_id if profile else None,
        **stats,
    }


@router.get("/me/dashboard-link")
async def get_stripe_dashboard_link(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a Stripe Express dashboard link for the seller."""
    profile = await listing_service.get_seller_profile(db, current_user.id)
    if not profile or not profile.stripe_account_id:
        raise HTTPException(400, "No seller account found")
    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe not configured")
    url = await get_seller_dashboard_link(
        profile.stripe_account_id,
        f"{settings.frontend_url}/seller/dashboard",
    )
    return {"url": url}


@router.get("/{seller_id}")
async def get_seller_profile(seller_id: int, db: AsyncSession = Depends(get_db)):
    """Public seller profile."""
    result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == seller_id))
    profile = result.scalar_one_or_none()
    if not profile or not profile.onboarding_complete:
        raise HTTPException(404, "Seller not found")

    from app.models.user import User as UserModel
    user = await db.get(UserModel, seller_id)
    stats = await listing_service.get_seller_stats(db, seller_id)
    return {
        "seller_id": seller_id,
        "email": user.email if user else None,
        **stats,
    }
