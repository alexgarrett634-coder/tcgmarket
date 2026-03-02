import asyncio
import httpx
from app.config import settings

PRICECHARTING_BASE = "https://www.pricecharting.com/api"
TTL_HOURS = 6.0


async def get_product_price(product_id: str) -> dict | None:
    if not settings.pricecharting_api_key:
        return None
    await asyncio.sleep(1.0)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{PRICECHARTING_BASE}/product",
            params={"id": product_id, "t": settings.pricecharting_api_key},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "loose_price": data.get("loose-price", 0) / 100,
            "cib_price": data.get("cib-price", 0) / 100,
            "new_price": data.get("new-price", 0) / 100,
        }
