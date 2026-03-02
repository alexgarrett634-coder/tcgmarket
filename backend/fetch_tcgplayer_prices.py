"""Fetch real TCGPlayer market prices from pokemontcg.io for all English cards.

Uses set-based queries (~150 total API calls instead of 20,000+) to stay
well within the free-tier rate limit.

Saves prices to card_prices table (source="tcgplayer", price_type="market").
Idempotent: skips cards already fetched in the last 7 days.

Usage:
    cd backend
    python fetch_tcgplayer_prices.py

After this completes, re-run seed_listings.py to use the real prices.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import engine, create_tables
from app.models.card import Card
from app.models.price import CardPrice
from app.config import settings

BASE = "https://api.pokemontcg.io/v2"
# Conservative concurrency — be polite to the free tier
SEM = asyncio.Semaphore(3)


def _headers() -> dict:
    h = {}
    if settings.pokemontcg_api_key:
        h["X-Api-Key"] = settings.pokemontcg_api_key
    return h


def _extract_price(tcgplayer: dict | None) -> float | None:
    """Return the best available TCGPlayer market price, or None."""
    if not tcgplayer:
        return None
    prices = tcgplayer.get("prices", {})
    # Prefer in this order: normal → holofoil → reverseHolofoil → 1st edition holofoil
    for price_type in ("normal", "holofoil", "reverseHolofoil", "1stEditionHolofoil", "unlimitedHolofoil"):
        market = prices.get(price_type, {}).get("market")
        if market and float(market) > 0:
            return float(market)
    return None


async def fetch_set_cards(client: httpx.AsyncClient, set_code: str) -> list[dict]:
    """Fetch all cards (with TCGPlayer prices) for a given set code."""
    results: list[dict] = []
    page = 1
    while True:
        async with SEM:
            try:
                resp = await client.get(
                    f"{BASE}/cards",
                    params={
                        "q": f"set.id:{set_code}",
                        "pageSize": 250,
                        "page": page,
                        # No 'select' restriction so we get tcgplayer price data
                    },
                    headers=_headers(),
                    timeout=20.0,
                )
            except Exception as exc:
                print(f"\n  Network error on {set_code} page {page}: {exc}")
                break

        if resp.status_code == 429:
            print(f"\n  Rate limited on {set_code}. Sleeping 60s …")
            await asyncio.sleep(60)
            continue
        if resp.status_code != 200:
            print(f"\n  HTTP {resp.status_code} for {set_code} — skipping.")
            break

        data = resp.json()
        cards = data.get("data", [])
        if not cards:
            break
        results.extend(cards)
        total_count = data.get("totalCount", 0)
        if len(results) >= total_count or len(cards) < 250:
            break
        page += 1
        await asyncio.sleep(0.4)  # polite inter-page delay

    return results


async def main() -> None:
    await create_tables()

    async with AsyncSession(engine, expire_on_commit=False) as db:
        # Discover all unique English set codes stored in our DB
        set_result = await db.execute(
            select(Card.set_code).where(Card.language == "en").distinct()
        )
        set_codes = [row[0] for row in set_result.all()]
        print(f"Found {len(set_codes)} unique English set codes in DB.")

        # Build set of card IDs that already have a recent tcgplayer price
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_result = await db.execute(
            select(CardPrice.card_id)
            .where(CardPrice.source == "tcgplayer", CardPrice.recorded_at >= cutoff)
        )
        already_fetched: set[str] = {row[0] for row in recent_result.all()}
        if already_fetched:
            print(f"  Skipping {len(already_fetched)} cards with prices fetched in the last 7 days.")

        total_saved = 0
        total_no_price = 0
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient() as client:
            for i, set_code in enumerate(sorted(set_codes)):
                label = f"[{i+1}/{len(set_codes)}] {set_code}"
                print(f"{label}...", end=" ", flush=True)

                cards = await fetch_set_cards(client, set_code)
                if not cards:
                    print("no cards returned.")
                    continue

                new_for_set = 0
                for card in cards:
                    card_id = card.get("id", "")
                    if not card_id or card_id in already_fetched:
                        continue

                    price = _extract_price(card.get("tcgplayer"))
                    if price is None:
                        total_no_price += 1
                        continue

                    db.add(CardPrice(
                        card_id=card_id,
                        source="tcgplayer",
                        price_type="market",
                        price_usd=price,
                        recorded_at=now,
                    ))
                    already_fetched.add(card_id)
                    new_for_set += 1
                    total_saved += 1

                if new_for_set > 0:
                    await db.commit()

                print(f"{len(cards)} cards fetched, {new_for_set} prices saved.")

                # Polite delay between sets (~1 request every 0.4s)
                await asyncio.sleep(0.4)

    print(f"\n{'='*50}")
    print(f"Done!")
    print(f"  Real TCGPlayer prices saved : {total_saved:,}")
    print(f"  Cards with no TCGPlayer data: {total_no_price:,} (will use heuristic fallback)")
    print(f"\nNext step: run  python seed_listings.py  to regenerate listings with real prices.")


if __name__ == "__main__":
    asyncio.run(main())
