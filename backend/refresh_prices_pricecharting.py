"""Batch-fetch real market prices from PriceCharting.com for all cards and sealed products.

PriceCharting has accurate Pokemon TCG prices including raw (NM) and PSA graded prices.

Requirements:
  - Set PRICECHARTING_API_KEY in backend/.env
  - Get a free API key at: https://www.pricecharting.com/api

Usage:
  cd backend
  python refresh_prices_pricecharting.py

What it does:
  1. Searches PriceCharting for each card by name + set
  2. Fetches raw NM price + PSA grade prices (6–10)
  3. Stores results as CardPrice(source="pricecharting") in the DB
  4. Updates sealed product prices that have a pricecharting_id set
  5. Prints detailed progress + coverage stats at the end
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, create_tables
from app.models.card import Card
from app.models.price import CardPrice, ProductPrice
from app.models.product import SealedProduct

PC_BASE = "https://www.pricecharting.com/api"
CONCURRENCY = 5          # Keep low — PriceCharting rate-limits aggressively
BATCH_COMMIT = 100

# ── Set code → PriceCharting console-name mapping ────────────────────────────
# PriceCharting uses "Pokemon <Set Name>" as the console/platform name.
SET_CODE_TO_PC_CONSOLE: dict[str, str] = {
    # WOTC era
    "base1":    "Pokemon Base Set",
    "jungle":   "Pokemon Jungle",
    "fossil":   "Pokemon Fossil",
    "base2":    "Pokemon Base Set 2",
    "teamrocket": "Pokemon Team Rocket",
    "gym1":     "Pokemon Gym Heroes",
    "gym2":     "Pokemon Gym Challenge",
    "neo1":     "Pokemon Neo Genesis",
    "neo2":     "Pokemon Neo Discovery",
    "neo3":     "Pokemon Neo Revelation",
    "neo4":     "Pokemon Neo Destiny",
    "lc":       "Pokemon Legendary Collection",
    "ecard1":   "Pokemon Expedition Base Set",
    "ecard2":   "Pokemon Aquapolis",
    "ecard3":   "Pokemon Skyridge",
    # EX era
    "ex1":      "Pokemon Ruby and Sapphire",
    "ex2":      "Pokemon Sandstorm",
    "ex3":      "Pokemon Dragon",
    "ex4":      "Pokemon Team Magma vs Team Aqua",
    "ex5":      "Pokemon Hidden Legends",
    "ex6":      "Pokemon FireRed and LeafGreen",
    "ex7":      "Pokemon Team Rocket Returns",
    "ex8":      "Pokemon Deoxys",
    "ex9":      "Pokemon Emerald",
    "ex10":     "Pokemon Unseen Forces",
    "ex11":     "Pokemon Delta Species",
    "ex12":     "Pokemon Legend Maker",
    "ex13":     "Pokemon Holon Phantoms",
    "ex14":     "Pokemon Crystal Guardians",
    "ex15":     "Pokemon Dragon Frontiers",
    "ex16":     "Pokemon Power Keepers",
    # Diamond & Pearl era
    "dp1":      "Pokemon Diamond and Pearl",
    "dp2":      "Pokemon Mysterious Treasures",
    "dp3":      "Pokemon Secret Wonders",
    "dp4":      "Pokemon Great Encounters",
    "dp5":      "Pokemon Majestic Dawn",
    "dp6":      "Pokemon Legends Awakened",
    "dp7":      "Pokemon Stormfront",
    "pl1":      "Pokemon Platinum",
    "pl2":      "Pokemon Rising Rivals",
    "pl3":      "Pokemon Supreme Victors",
    "pl4":      "Pokemon Arceus",
    "hgss1":    "Pokemon HeartGold and SoulSilver",
    "hgss2":    "Pokemon Unleashed",
    "hgss3":    "Pokemon Undaunted",
    "hgss4":    "Pokemon Triumphant",
    "col1":     "Pokemon Call of Legends",
    # Black & White era
    "bw1":      "Pokemon Black and White",
    "bw2":      "Pokemon Emerging Powers",
    "bw3":      "Pokemon Noble Victories",
    "bw4":      "Pokemon Next Destinies",
    "bw5":      "Pokemon Dark Explorers",
    "bw6":      "Pokemon Dragons Exalted",
    "bw7":      "Pokemon Boundaries Crossed",
    "bw8":      "Pokemon Plasma Storm",
    "bw9":      "Pokemon Plasma Freeze",
    "bw10":     "Pokemon Plasma Blast",
    "bw11":     "Pokemon Legendary Treasures",
    # XY era
    "xy1":      "Pokemon XY",
    "xy2":      "Pokemon Flashfire",
    "xy3":      "Pokemon Furious Fists",
    "xy4":      "Pokemon Phantom Forces",
    "xy5":      "Pokemon Primal Clash",
    "xy6":      "Pokemon Roaring Skies",
    "xy7":      "Pokemon Ancient Origins",
    "xy8":      "Pokemon BREAKthrough",
    "xy9":      "Pokemon BREAKpoint",
    "xy10":     "Pokemon Fates Collide",
    "xy11":     "Pokemon Steam Siege",
    "xy12":     "Pokemon Evolutions",
    # Sun & Moon era
    "sm1":      "Pokemon Sun and Moon",
    "sm2":      "Pokemon Guardians Rising",
    "sm3":      "Pokemon Burning Shadows",
    "sm35":     "Pokemon Shining Legends",
    "sm4":      "Pokemon Crimson Invasion",
    "sm5":      "Pokemon Ultra Prism",
    "sm6":      "Pokemon Forbidden Light",
    "sm7":      "Pokemon Celestial Storm",
    "sm75":     "Pokemon Dragon Majesty",
    "sm8":      "Pokemon Lost Thunder",
    "sm9":      "Pokemon Team Up",
    "sm10":     "Pokemon Unbroken Bonds",
    "sm11":     "Pokemon Unified Minds",
    "sm115":    "Pokemon Hidden Fates",
    "sm12":     "Pokemon Cosmic Eclipse",
    # Sword & Shield era
    "swsh1":    "Pokemon Sword and Shield",
    "swsh2":    "Pokemon Rebel Clash",
    "swsh3":    "Pokemon Darkness Ablaze",
    "swsh35":   "Pokemon Champion's Path",
    "swsh4":    "Pokemon Vivid Voltage",
    "swsh45":   "Pokemon Shining Fates",
    "swsh5":    "Pokemon Battle Styles",
    "swsh6":    "Pokemon Chilling Reign",
    "swsh7":    "Pokemon Evolving Skies",
    "swsh8":    "Pokemon Fusion Strike",
    "swsh9":    "Pokemon Brilliant Stars",
    "swsh10":   "Pokemon Astral Radiance",
    "swsh105":  "Pokemon Pokemon GO",
    "swsh11":   "Pokemon Lost Origin",
    "swsh12":   "Pokemon Silver Tempest",
    "swsh125":  "Pokemon Crown Zenith",
    # Scarlet & Violet era
    "sv1":      "Pokemon Scarlet and Violet",
    "sv2":      "Pokemon Paldea Evolved",
    "sv3":      "Pokemon Obsidian Flames",
    "sv35":     "Pokemon 151",
    "sv4":      "Pokemon Paradox Rift",
    "sv45":     "Pokemon Paldean Fates",
    "sv5":      "Pokemon Temporal Forces",
    "sv6":      "Pokemon Twilight Masquerade",
    "sv65":     "Pokemon Shrouded Fable",
    "sv7":      "Pokemon Stellar Crown",
    "sv8":      "Pokemon Surging Sparks",
    "sv9":      "Pokemon Prismatic Evolutions",
}

PSA_GRADE_FIELDS = {
    10: "grade-10-price",
    9:  "grade-9-price",
    8:  "grade-8-price",
    7:  "grade-7-price",
    6:  "grade-6-price",
}


def _cents_to_usd(cents: int | None) -> float | None:
    if not cents or cents <= 0:
        return None
    return round(cents / 100, 2)


async def search_card(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    card: Card,
) -> dict | None:
    """Search PriceCharting for a card; return the best-matching product JSON or None."""
    console = SET_CODE_TO_PC_CONSOLE.get(card.set_code.lower())
    if not console:
        return None  # Unknown set — skip

    query = f"{card.name} {card.number or ''}".strip()
    async with sem:
        try:
            r = await client.get(
                f"{PC_BASE}/products",
                params={"q": query, "t": settings.pricecharting_api_key},
                timeout=15.0,
            )
            if r.status_code != 200:
                return None
            products = r.json().get("products", [])
            # Find best match: same console AND name contains card name
            name_lower = card.name.lower()
            console_lower = console.lower()
            for p in products:
                if (
                    p.get("console-name", "").lower() == console_lower
                    and name_lower in p.get("product-name", "").lower()
                ):
                    return p
            # Looser fallback: console match only, first result
            for p in products:
                if p.get("console-name", "").lower() == console_lower:
                    return p
        except Exception:
            pass
    return None


async def fetch_product_detail(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    product_id: str,
) -> dict | None:
    """Fetch full product detail (includes grade prices) by PriceCharting product ID."""
    async with sem:
        try:
            r = await client.get(
                f"{PC_BASE}/product",
                params={"id": product_id, "t": settings.pricecharting_api_key},
                timeout=15.0,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return None


async def refresh_cards(db: AsyncSession, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> tuple[int, int]:
    """Fetch and store PriceCharting prices for all English cards. Returns (found, missing)."""
    result = await db.execute(select(Card).where(Card.language == "en"))
    cards = result.scalars().all()
    print(f"Processing {len(cards):,} English cards...")

    now = datetime.now(timezone.utc)
    found = 0
    missing = 0
    committed = 0

    for i, card in enumerate(cards):
        # Phase 1: search for the card
        match = await search_card(client, sem, card)
        if not match:
            missing += 1
            if (i + 1) % 500 == 0:
                pct = int((i + 1) / len(cards) * 100)
                print(f"  {i+1:,}/{len(cards):,} ({pct}%) — {found:,} found, {missing:,} missing")
            continue

        pc_id = str(match["id"])

        # Phase 2: fetch full detail for graded prices
        detail = await fetch_product_detail(client, sem, pc_id)
        data = detail if detail else match

        raw_price = _cents_to_usd(data.get("loose-price"))
        if raw_price:
            db.add(CardPrice(
                card_id=card.id,
                source="pricecharting",
                price_type="market",
                price_usd=raw_price,
                recorded_at=now,
            ))
            found += 1

        for grade, field in PSA_GRADE_FIELDS.items():
            grade_price = _cents_to_usd(data.get(field))
            if grade_price:
                db.add(CardPrice(
                    card_id=card.id,
                    source="pricecharting",
                    price_type=f"psa{grade}",
                    price_usd=grade_price,
                    recorded_at=now,
                ))

        committed += 1
        if committed >= BATCH_COMMIT:
            await db.commit()
            committed = 0

        if (i + 1) % 500 == 0:
            pct = int((i + 1) / len(cards) * 100)
            print(f"  {i+1:,}/{len(cards):,} ({pct}%) — {found:,} found, {missing:,} missing")

    if committed:
        await db.commit()

    return found, missing


async def refresh_sealed_products(db: AsyncSession, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> int:
    """Fetch PriceCharting prices for sealed products that have a pricecharting_id."""
    result = await db.execute(
        select(SealedProduct).where(SealedProduct.pricecharting_id.isnot(None))
    )
    products = result.scalars().all()
    print(f"\nProcessing {len(products):,} sealed products with PriceCharting IDs...")

    now = datetime.now(timezone.utc)
    updated = 0

    for product in products:
        detail = await fetch_product_detail(client, sem, product.pricecharting_id)
        if not detail:
            continue

        for price_type, field in [("loose", "loose-price"), ("new", "new-price")]:
            val = _cents_to_usd(detail.get(field))
            if val:
                db.add(ProductPrice(
                    product_id=product.id,
                    source="pricecharting",
                    price_type=price_type,
                    price_usd=val,
                    recorded_at=now,
                ))
        updated += 1

    await db.commit()
    return updated


async def main() -> None:
    if not settings.pricecharting_api_key:
        print("ERROR: PRICECHARTING_API_KEY is not set in backend/.env")
        print()
        print("Get a free API key at: https://www.pricecharting.com/api")
        print("Then add to backend/.env:")
        print("  PRICECHARTING_API_KEY=your_key_here")
        print()
        print("After adding the key, re-run this script.")
        return

    await create_tables()
    print(f"PriceCharting batch price refresh")
    print(f"Concurrency: {CONCURRENCY}  |  Batch commit: {BATCH_COMMIT}\n")

    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            found, missing = await refresh_cards(db, client, sem)
            sealed_updated = await refresh_sealed_products(db, client, sem)

    total = found + missing
    coverage = round(found / total * 100, 1) if total else 0
    print(f"\n{'='*50}")
    print(f"Cards with PriceCharting prices: {found:,} / {total:,} ({coverage}%)")
    print(f"Cards without match:             {missing:,}")
    print(f"Sealed products updated:         {sealed_updated:,}")
    print(f"\nNext step: run  python seed_listings.py  to regenerate listings with new prices.")


if __name__ == "__main__":
    asyncio.run(main())
