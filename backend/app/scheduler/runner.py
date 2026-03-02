"""APScheduler setup — starts/stops with FastAPI lifespan."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import (
    job_refresh_prices,
    job_scan_ebay_deals,
    job_evaluate_alerts,
    job_update_active_listing_prices,
    job_generate_internal_deals,
)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")

        _scheduler.add_job(job_refresh_prices,                "interval", minutes=30,  id="refresh_prices")
        _scheduler.add_job(job_scan_ebay_deals,               "interval", seconds=60,  id="scan_ebay_deals")
        _scheduler.add_job(job_evaluate_alerts,               "interval", minutes=15,  id="evaluate_alerts")
        _scheduler.add_job(job_update_active_listing_prices,  "interval", seconds=60,  id="update_active_prices")
        _scheduler.add_job(job_generate_internal_deals,       "interval", seconds=300, id="generate_internal_deals")

    return _scheduler


def start_scheduler() -> None:
    get_scheduler().start()


def stop_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
