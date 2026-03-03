"""Insights router: eBay-based price predictions (requires Insights or Pro subscription)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.services.tier_service import get_user_tier, tier_gte
from app.services.insights_service import predict_card_value

router = APIRouter(prefix="/insights", tags=["insights"])


async def _require_insights(db: AsyncSession, user: User) -> None:
    tier = await get_user_tier(db, user.id)
    if not tier_gte(tier, "insights"):
        raise HTTPException(403, "Insights subscription required. Subscribe for $10/month to unlock price predictions.")


@router.get("/predict/{card_id:path}")
async def predict_price(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Predict card value based on eBay active listings and release-date decay model."""
    await _require_insights(db, current_user)
    result = await predict_card_value(db, card_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result
