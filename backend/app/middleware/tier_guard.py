from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.tier_service import get_user_tier, TIER_ORDER


def require_tier(*allowed_tiers: str):
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_tier = await get_user_tier(db, current_user.id)
        user_level = TIER_ORDER.get(user_tier, 0)
        required_level = min(TIER_ORDER.get(t, 0) for t in allowed_tiers)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "upgrade_required",
                    "required_tier": allowed_tiers[0],
                    "current_tier": user_tier,
                },
            )
        return current_user
    return dependency
