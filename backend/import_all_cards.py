"""Bulk import all physical Pokemon TCG cards in 8 languages using tcgdex.net API.

Filters OUT Pokemon TCG Pocket (mobile game) cards — identified by '/tcgp/' in image URLs.
Fetches individual card data to get rarity for accurate pricing.

Card ID scheme:
  English:      {tcgdex_id}         e.g. "sv01-001"
  Other langs:  {tcgdex_id}-{lang}  e.g. "sv01-001-ja"

Usage:
  cd backend
  python import_all_cards.py              # all languages
  python import_all_cards.py --lang en    # English only
  python import_all_cards.py --lang ja,ko # specific languages
"""
import asyncio
import os
import sys
import argparse
from datetime import datetime

import httpx

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

def _make_upsert(db_url: str):
    if "postgresql" in db_url or "postgres" in db_url:
        return pg_insert
    return sqlite_insert

from app.database import engine, create_tables
from app.models.card import Card

TCGDEX_BASE = "https://api.tcgdex.net/v2/{lang}"

LANGUAGES = ["en", "fr", "de", "es", "it", "pt", "ja", "ko"]

LANG_NAMES = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean",
}

# Semaphore to limit concurrent card-detail requests
RARITY_CONCURRENCY = 15


async def migrate(conn):
    """Add language column if it doesn't exist."""
    try:
        await conn.execute(text("ALTER TABLE cards ADD COLUMN language TEXT NOT NULL DEFAULT 'en'"))
        print("Added column: language")
    except Exception:
        pass  # already exists


def is_tcgp_image(image_url: str | None) -> bool:
    """TCG Pocket cards have '/tcgp/' in their image URL path."""
    return bool(image_url and "/tcgp/" in image_url)


async def fetch_card_rarity(client: httpx.AsyncClient, sem: asyncio.Semaphore, lang: str, card_id: str) -> str | None:
    """Fetch individual card data to get rarity. Returns rarity string or None."""
    async with sem:
        try:
            r = await client.get(f"{TCGDEX_BASE.format(lang=lang)}/cards/{card_id}", timeout=15.0)
            if r.status_code == 200:
                data = r.json()
                return data.get("rarity")
        except Exception:
            pass
    return None


async def import_language(client: httpx.AsyncClient, db: AsyncSession, lang: str) -> int:
    base = TCGDEX_BASE.format(lang=lang)
    lang_name = LANG_NAMES.get(lang, lang)

    print(f"\n[{lang_name}] Fetching set list...")
    try:
        r = await client.get(f"{base}/sets", timeout=30.0)
        r.raise_for_status()
        sets = r.json()
    except Exception as e:
        print(f"[{lang_name}] ERROR fetching sets: {e}")
        return 0

    print(f"[{lang_name}] Found {len(sets)} sets.")
    total_cards = 0
    skipped_tcgp = 0
    sem = asyncio.Semaphore(RARITY_CONCURRENCY)

    for i, s in enumerate(sets, 1):
        set_id = s["id"]
        set_name = s["name"]

        try:
            r2 = await client.get(f"{base}/sets/{set_id}", timeout=30.0)
            if r2.status_code != 200:
                continue
            set_data = r2.json()
        except Exception:
            continue

        cards = set_data.get("cards", [])
        if not cards:
            continue

        # Detect TCGP sets by checking first card's image URL
        first_image = cards[0].get("image") if cards else None
        if is_tcgp_image(first_image):
            skipped_tcgp += len(cards)
            continue

        now = datetime.utcnow()

        # Fetch rarities concurrently for all cards in this set
        raw_ids = [c.get("id", "") for c in cards if c.get("id") and c.get("name")]
        rarity_tasks = [fetch_card_rarity(client, sem, lang, rid) for rid in raw_ids]
        rarities = await asyncio.gather(*rarity_tasks)
        rarity_map = dict(zip(raw_ids, rarities))

        count = 0
        for c in cards:
            raw_id = c.get("id", "")
            name = c.get("name", "")
            local_id = c.get("localId", "")
            tcg_image = c.get("image")
            img_small = (tcg_image + "/low.png") if tcg_image else None
            img_large = (tcg_image + "/high.png") if tcg_image else None

            if not raw_id or not name:
                continue
            if is_tcgp_image(img_small):
                continue

            card_id = raw_id if lang == "en" else f"{raw_id}-{lang}"
            rarity = rarity_map.get(raw_id)

            _insert = _make_upsert(str(engine.url))
            stmt = _insert(Card).values(
                id=card_id,
                name=name,
                set_name=set_name,
                set_code=set_id,
                number=local_id or None,
                rarity=rarity,
                supertype=None,
                subtypes=None,
                image_small=img_small,
                image_large=img_large,
                language=lang,
                fetched_at=now,
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": name,
                    "set_name": set_name,
                    "rarity": rarity,
                    "image_small": img_small,
                    "image_large": img_large,
                    "language": lang,
                    "fetched_at": now,
                },
            )
            await db.execute(stmt)
            count += 1

        await db.commit()
        total_cards += count
        pct = int(i / len(sets) * 100)
        print(f"  [{lang}] [{i}/{len(sets)}] {pct}% -- {set_name} ({set_id}): {count} cards, rarity fetched (total: {total_cards})")

    if skipped_tcgp:
        print(f"  [{lang}] Skipped {skipped_tcgp} TCG Pocket cards (mobile game, not physical TCG)")
    return total_cards


async def import_all(langs: list[str]):
    print("Creating tables if needed...")
    await create_tables()

    async with engine.begin() as conn:
        await migrate(conn)

    grand_total = 0

    # Use a single long-lived client for all requests
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            for lang in langs:
                count = await import_language(client, db, lang)
                grand_total += count
                print(f"  [{LANG_NAMES.get(lang, lang)}] Done: {count:,} physical TCG cards imported")

    print(f"\nAll done! Imported {grand_total:,} physical TCG cards across {len(langs)} language(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="", help="Comma-separated language codes (default: all)")
    args = parser.parse_args()

    if args.lang:
        langs = [l.strip() for l in args.lang.split(",") if l.strip() in LANGUAGES]
        if not langs:
            print(f"Invalid language(s). Valid: {', '.join(LANGUAGES)}")
            sys.exit(1)
    else:
        langs = LANGUAGES

    asyncio.run(import_all(langs))
