import asyncio
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.price import PriceFetchLog


async def is_stale(db: AsyncSession, item_type: str, item_id: str, source: str, ttl_hours: float) -> bool:
    result = await db.execute(
        select(PriceFetchLog).where(
            PriceFetchLog.item_type == item_type,
            PriceFetchLog.item_id == item_id,
            PriceFetchLog.source == source,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
    last = log.last_fetched_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last < cutoff


async def update_fetch_log(db: AsyncSession, item_type: str, item_id: str, source: str, status: str = "ok") -> None:
    result = await db.execute(
        select(PriceFetchLog).where(
            PriceFetchLog.item_type == item_type,
            PriceFetchLog.item_id == item_id,
            PriceFetchLog.source == source,
        )
    )
    log = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if log:
        log.last_fetched_at = now
        log.fetch_status = status
    else:
        db.add(PriceFetchLog(
            item_type=item_type,
            item_id=item_id,
            source=source,
            last_fetched_at=now,
            fetch_status=status,
        ))


async def fetch_with_retry(url: str, headers: dict | None = None, params: dict | None = None, max_retries: int = 1) -> dict | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(max_retries + 1):
            try:
                resp = await client.get(url, headers=headers or {}, params=params or {})
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    await asyncio.sleep(2.0)
                    continue
                if resp.status_code == 200:
                    return resp.json()
                return None
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < max_retries:
                    await asyncio.sleep(2.0)
                    continue
                return None
    return None
