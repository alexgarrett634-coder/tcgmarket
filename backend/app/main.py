import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables, migrate_schema, AsyncSessionLocal
from app.scheduler.runner import start_scheduler, stop_scheduler
from app.routers import (
    auth, cards, products, listings, orders, sellers, deals,
    watchlist, portfolio, notifications, wallet,
    billing, api_keys, ygo, onepiece, insights,
)


async def _populate_set_dates_bg():
    """Background task: populate Pokemon set release dates from pokemontcg.io."""
    try:
        from app.fetchers.pokemontcg import populate_set_dates
        async with AsyncSessionLocal() as db:
            await populate_set_dates(db)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await migrate_schema()
    asyncio.create_task(_populate_set_dates_bg())
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="PokéMarket API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth.router,          prefix=PREFIX)
app.include_router(cards.router,         prefix=PREFIX)
app.include_router(products.router,      prefix=PREFIX)
app.include_router(listings.router,      prefix=PREFIX)
app.include_router(orders.router,        prefix=PREFIX)
app.include_router(sellers.router,       prefix=PREFIX)
app.include_router(deals.router,         prefix=PREFIX)
app.include_router(watchlist.router,     prefix=PREFIX)
app.include_router(portfolio.router,     prefix=PREFIX)
app.include_router(notifications.router, prefix=PREFIX)
app.include_router(wallet.router,        prefix=PREFIX)
app.include_router(billing.router,       prefix=PREFIX)
app.include_router(api_keys.router,      prefix=PREFIX)
app.include_router(ygo.router,            prefix=PREFIX)
app.include_router(onepiece.router,       prefix=PREFIX)
app.include_router(insights.router,       prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
