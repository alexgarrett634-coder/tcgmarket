"""Pokemon TCG API (pokemontcg.io) fetcher."""
from datetime import datetime, date
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


async def fetch_card_prices(card_id: str) -> dict[str, float]:
    """Fetch TCGPlayer prices for a single card via pokemontcg.io.
    Returns {price_type: price_usd} e.g. {"market": 2.50, "near_mint": 1.00}.
    """
    data = await fetch_with_retry(f"{BASE}/cards/{card_id}", headers=_headers())
    if not data:
        return {}
    tcg = data.get("data", {}).get("tcgplayer", {}).get("prices", {})
    result: dict[str, float] = {}
    # Prefer holofoil > 1stEditionHolofoil > reverseHolofoil > normal
    for variant in ("holofoil", "1stEditionHolofoil", "reverseHolofoil", "normal"):
        v = tcg.get(variant, {})
        if v.get("market") and "market" not in result:
            result["market"] = float(v["market"])
        if v.get("low") and "near_mint" not in result:
            result["near_mint"] = float(v["low"])
        if result.get("market") and result.get("near_mint"):
            break
    return result


async def fetch_sets() -> dict[str, date]:
    """Fetch all Pokemon TCG sets and return {set_code: release_date}."""
    data = await fetch_with_retry(f"{BASE}/sets", headers=_headers(), params={"pageSize": 500})
    if not data:
        return {}
    result: dict[str, date] = {}
    for s in data.get("data", []):
        raw_date = s.get("releaseDate", "")  # format: "YYYY/MM/DD"
        if raw_date and s.get("id"):
            try:
                parts = raw_date.replace("-", "/").split("/")
                result[s["id"]] = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                pass
    return result


async def populate_set_dates(db: Any) -> None:
    """Populate set_release_date on all Pokemon cards using pokemontcg.io set data."""
    from sqlalchemy import update
    from app.models.card import Card

    set_dates = await fetch_sets()
    if not set_dates:
        return
    for set_code, release_date in set_dates.items():
        await db.execute(
            update(Card)
            .where(Card.set_code == set_code, Card.language == "en")
            .values(set_release_date=release_date)
        )
    await db.commit()


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
