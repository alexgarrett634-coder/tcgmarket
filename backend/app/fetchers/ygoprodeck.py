"""
Fetch Yu-Gi-Oh! card info from the ygoprodeck.com public API.
Used to enrich YGO cards with images, ATK/DEF, type, and description.

API docs: https://ygoprodeck.com/api-guide/
"""
import urllib.parse

import httpx

_BASE = "https://db.ygoprodeck.com/api/v7/cardinfo.php"


async def fetch_ygo_card_info(name: str) -> dict | None:
    """
    Fetch card data by exact name from ygoprodeck.com.
    Returns a dict with image URLs and card stats, or None on failure.
    """
    url = f"{_BASE}?name={urllib.parse.quote(name)}"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(url, headers={"User-Agent": "PokéMarket/1.0"})
        if r.status_code != 200:
            return None
        payload = r.json()
        data = payload.get("data", [])
        if not data:
            return None
        card = data[0]
        images = card.get("card_images", [{}])
        img = images[0] if images else {}
        return {
            "image_small": img.get("image_url_small"),
            "image_large": img.get("image_url"),
            "card_type": card.get("type"),
            "attribute": card.get("attribute"),
            "race": card.get("race"),
            "atk": card.get("atk"),
            "def": card.get("def"),
            "desc": card.get("desc"),
        }
    except Exception:
        return None
