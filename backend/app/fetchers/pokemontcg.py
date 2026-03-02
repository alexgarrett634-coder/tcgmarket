"""Pokemon TCG API (pokemontcg.io) fetcher."""
from datetime import datetime
from typing import Any

from app.config import settings
from app.fetchers.base import fetch_with_retry

BASE = "https://api.pokemontcg.io/v2"


def _headers() -> dict:
    h = {}
    if settings.pokemontcg_api_key:
        h["X-Api-Key"] = settings.pokemontcg_api_key
    return h


async def search_cards(q: str, page: int = 1, page_size: int = 20) -> list[dict]:
    url = f"{BASE}/cards"
    params = {
        "q": f"name:{q}*",
        "page": page,
        "pageSize": page_size,
        "select": "id,name,set,number,rarity,supertype,subtypes,images",
    }
    data = await fetch_with_retry(url, headers=_headers(), params=params)
    if not data:
        return []
    return [_card_to_dict(c) for c in data.get("data", [])]


async def get_card(card_id: str) -> dict | None:
    url = f"{BASE}/cards/{card_id}"
    data = await fetch_with_retry(url, headers=_headers())
    if not data:
        return None
    raw = data.get("data", {})
    return _card_to_dict(raw) if raw else None


def _card_to_dict(c: dict) -> dict:
    images = c.get("images", {})
    return {
        "id": c.get("id", ""),
        "name": c.get("name", ""),
        "set_name": c.get("set", {}).get("name", ""),
        "set_code": c.get("set", {}).get("id", ""),
        "number": c.get("number"),
        "rarity": c.get("rarity"),
        "supertype": c.get("supertype"),
        "subtypes": ",".join(c.get("subtypes") or []),
        "image_small": images.get("small"),
        "image_large": images.get("large"),
    }


async def upsert_card(db: Any, data: dict) -> None:
    """Insert or update a Card in the database via SQLite UPSERT."""
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    from app.models.card import Card

    stmt = sqlite_insert(Card).values(
        id=data["id"],
        name=data["name"],
        set_name=data["set_name"],
        set_code=data["set_code"],
        number=data.get("number"),
        rarity=data.get("rarity"),
        supertype=data.get("supertype"),
        subtypes=data.get("subtypes"),
        image_small=data.get("image_small"),
        image_large=data.get("image_large"),
        fetched_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["id"],
        set_={
            "name": data["name"],
            "image_small": data.get("image_small"),
            "image_large": data.get("image_large"),
            "fetched_at": datetime.utcnow(),
        },
    )
    await db.execute(stmt)
