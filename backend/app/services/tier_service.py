from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from datetime import date

from app.models.subscription import Subscription, UsageTracking
from app.config import settings


TIER_ORDER = {"free": 0, "pro": 1, "enterprise": 2}


async def get_user_tier(db: AsyncSession, user_id: int) -> str:
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    sub = result.scalar_one_or_none()
    if sub is None or sub.status not in ("active", "trialing"):
        return "free"
    return sub.tier


def tier_gte(tier: str, required: str) -> bool:
    return TIER_ORDER.get(tier, 0) >= TIER_ORDER.get(required, 0)


async def check_and_increment_search(db: AsyncSession, user_id: int, tier: str) -> bool:
    """Returns True if allowed, False if Free tier limit exceeded."""
    if tier_gte(tier, "pro"):
        return True

    today = date.today()
    result = await db.execute(
        select(UsageTracking).where(
            UsageTracking.user_id == user_id,
            UsageTracking.date == today,
        )
    )
    tracking = result.scalar_one_or_none()

    if tracking is None:
        tracking = UsageTracking(user_id=user_id, date=today, search_count=0)
        db.add(tracking)
        await db.flush()

    if tracking.search_count >= settings.free_tier_daily_searches:
        return False

    tracking.search_count += 1
    return True


async def get_price_history_days(tier: str) -> int:
    if tier == "enterprise":
        return 365
    if tier == "pro":
        return 90
    return 0


async def get_watchlist_limit(tier: str) -> int:
    if tier == "enterprise":
        return 999999
    if tier == "pro":
        return settings.pro_watchlist_limit
    return 0


async def get_deal_alert_limit(tier: str) -> int:
    if tier == "enterprise":
        return 999999
    if tier == "pro":
        return 50
    return 0
