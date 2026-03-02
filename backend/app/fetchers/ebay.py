import asyncio
import base64
import time
import httpx
from app.config import settings

EBAY_API_BASE = "https://api.ebay.com/buy/browse/v1"
EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

_token_cache: dict = {"token": None, "expires_at": 0}


async def get_oauth_token() -> str | None:
    if not settings.ebay_client_id or not settings.ebay_client_secret:
        return None
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]
    creds = base64.b64encode(f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()).decode()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            EBAY_TOKEN_URL,
            headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        )
        if resp.status_code == 200:
            data = resp.json()
            _token_cache["token"] = data["access_token"]
            _token_cache["expires_at"] = now + data.get("expires_in", 7200)
            return _token_cache["token"]
    return None


async def search_listings(query: str, limit: int = 10) -> list[dict]:
    token = await get_oauth_token()
    if not token:
        return []
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{EBAY_API_BASE}/item_summary/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "limit": limit, "filter": "buyingOptions:{FIXED_PRICE}"},
        )
        if resp.status_code != 200:
            return []
        items = resp.json().get("itemSummaries", [])
        results = []
        for item in items:
            price_info = item.get("price", {})
            price_val = float(price_info.get("value", 0))
            results.append({
                "external_id": item.get("itemId", ""),
                "title": item.get("title", ""),
                "price": price_val,
                "condition": item.get("condition", ""),
                "seller": item.get("seller", {}).get("username", ""),
                "url": item.get("itemWebUrl", ""),
            })
        return results
