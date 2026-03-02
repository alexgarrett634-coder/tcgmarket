from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.product import SealedProduct
from app.models.price import ProductPrice
from app.models.market import PredictionMarket
from app.fetchers import pricecharting
from app.services.tier_service import get_user_tier, get_price_history_days
from app.services.market_service import get_probability

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    q: str = Query("", description="Filter by name"),
    product_type: str = Query("", description="Filter by type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SealedProduct)
    if q:
        stmt = stmt.where(SealedProduct.name.ilike(f"%{q}%"))
    if product_type:
        stmt = stmt.where(SealedProduct.product_type == product_type)
    stmt = stmt.order_by(SealedProduct.name).limit(limit).offset(offset)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "set_name": p.set_name,
            "product_type": p.product_type,
            "image_url": p.image_url,
        }
        for p in products
    ]


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(SealedProduct, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return {
        "id": product.id,
        "name": product.name,
        "set_name": product.set_name,
        "product_type": product.product_type,
        "image_url": product.image_url,
        "pricecharting_id": product.pricecharting_id,
        "ebay_search_term": product.ebay_search_term,
    }


@router.get("/{product_id}/prices")
async def get_product_prices(
    product_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(SealedProduct, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    tier = "free"
    if current_user:
        tier = await get_user_tier(db, current_user.id)

    # Fetch from PriceCharting if Pro+
    if tier != "free" and product.pricecharting_id:
        pc_data = await pricecharting.get_product_price(product.pricecharting_id)
        if pc_data:
            from datetime import datetime
            for price_type, val in [("loose", pc_data["loose_price"]), ("cib", pc_data["cib_price"]), ("new", pc_data["new_price"])]:
                if val:
                    db.add(ProductPrice(
                        product_id=product_id,
                        source="pricecharting",
                        price_type=price_type,
                        price_usd=val,
                    ))
            await db.commit()

    history_days = get_price_history_days(tier)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=history_days)
    result = await db.execute(
        select(ProductPrice).where(
            ProductPrice.product_id == product_id,
            ProductPrice.recorded_at >= cutoff,
        ).order_by(ProductPrice.recorded_at.desc())
    )
    prices = result.scalars().all()

    return {
        "current": [
            {
                "source": p.source,
                "price_type": p.price_type,
                "price_usd": p.price_usd,
                "recorded_at": p.recorded_at.isoformat(),
            }
            for p in prices[:10]
        ],
        "history": [
            {"recorded_at": p.recorded_at.isoformat(), "price_usd": p.price_usd, "price_type": p.price_type}
            for p in reversed(prices)
        ],
        "history_days": history_days,
    }


@router.get("/{product_id}/markets")
async def get_product_markets(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PredictionMarket).where(
            PredictionMarket.product_id == product_id,
            PredictionMarket.status == "open",
        ).order_by(PredictionMarket.created_at.desc())
    )
    markets = result.scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "probability": get_probability(m.pool_yes, m.pool_no),
            "total_volume": m.total_volume,
            "target_date": m.target_date.isoformat(),
            "currency": m.currency,
        }
        for m in markets
    ]
