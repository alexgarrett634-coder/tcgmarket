"""Batch-fetch real TCGPlayer market prices from tcgdex for all English cards.

Calls GET https://api.tcgdex.net/v2/en/sets/{set_code}/{number} for each card
and stores the TCGPlayer normal/holofoil market price in card_prices.

Replaces stale heuristic placeholder prices with real market data.

Usage:
  cd backend
  python refresh_card_prices.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, create_tables
from app.models.card import Card
from app.models.price import CardPrice

TCGDEX_BASE = "https://api.tcgdex.net/v2/en"
CONCURRENCY = 15
BATCH_SIZE = 200


async def fetch_price(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    set_code: str,
    number: str,
) -> float | None:
    """Fetch TCGPlayer market price for one card. Returns USD price or None."""
    async with sem:
        try:
            r = await client.get(
                f"{TCGDEX_BASE}/sets/{set_code}/{number}",
                timeout=15.0,
            )
            if r.status_code == 200:
                data = r.json()
                tcgp = (data.get("prices") or {}).get("tcgplayer") or {}
                # Prefer normal market price; fall back to holofoil
                for field in ("normal", "holofoil", "reverseHolofoil"):
                    val = tcgp.get(field)
                    if val is not None:
                        return float(val)
        except Exception:
            pass
    return None


async def main() -> None:
    await create_tables()

    async with AsyncSession(engine, expire_on_commit=False) as db:
        result = await db.execute(
            select(Card).where(Card.language == "en")
        )
        cards = result.scalars().all()

    print(f"Fetching prices for {len(cards):,} English cards from tcgdex...")
    print(f"Concurrency: {CONCURRENCY}  |  Batch commit size: {BATCH_SIZE}\n")

    sem = asyncio.Semaphore(CONCURRENCY)
    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            fetch_price(client, sem, c.set_code, c.number or "1")
            for c in cards
        ]
        results = await asyncio.gather(*tasks)

    # Write results in batches
    found = 0
    missing = 0

    async with AsyncSession(engine, expire_on_commit=False) as db:
        for batch_start in range(0, len(cards), BATCH_SIZE):
            batch_cards = cards[batch_start:batch_start + BATCH_SIZE]
            batch_results = results[batch_start:batch_start + BATCH_SIZE]

            for card, price in zip(batch_cards, batch_results):
                if price is not None:
                    db.add(CardPrice(
                        card_id=card.id,
                        source="tcgplayer",
                        price_type="market",
                        price_usd=price,
                        recorded_at=now,
                    ))
                    found += 1
                else:
                    missing += 1

            await db.commit()

            done = batch_start + len(batch_cards)
            pct = int(done / len(cards) * 100)
            print(f"  {done:,}/{len(cards):,} ({pct}%) — {found:,} prices found, {missing:,} missing")

    print(f"\nDone!")
    print(f"  TCGPlayer prices stored: {found:,}")
    print(f"  Cards without price data: {missing:,} (heuristic will be used for these)")


if __name__ == "__main__":
    asyncio.run(main())
