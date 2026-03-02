"""
Seed the database with demo cards, 90-day price history, prediction markets, and deal listings.

Run from the backend/ directory:
    python seed_data.py
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

DATABASE_URL = "sqlite+aiosqlite:///./data/prices.db"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

random.seed(42)

# ---------------------------------------------------------------------------
# Card definitions: (id, name, set_name, set_code, number, rarity, supertype, image_small, image_large, base_price)
# ---------------------------------------------------------------------------
CARDS = [
    {
        "id": "base1-4",
        "name": "Charizard",
        "set_name": "Base Set",
        "set_code": "base1",
        "number": "4",
        "rarity": "Rare Holo",
        "supertype": "Pokémon",
        "subtypes": "Stage 2",
        "image_small": "https://images.pokemontcg.io/base1/4.png",
        "image_large": "https://images.pokemontcg.io/base1/4_hires.png",
        "base_price": 350.0,
    },
    {
        "id": "base1-58",
        "name": "Pikachu",
        "set_name": "Base Set",
        "set_code": "base1",
        "number": "58",
        "rarity": "Common",
        "supertype": "Pokémon",
        "subtypes": "Basic",
        "image_small": "https://images.pokemontcg.io/base1/58.png",
        "image_large": "https://images.pokemontcg.io/base1/58_hires.png",
        "base_price": 25.0,
    },
    {
        "id": "base1-10",
        "name": "Mewtwo",
        "set_name": "Base Set",
        "set_code": "base1",
        "number": "10",
        "rarity": "Rare Holo",
        "supertype": "Pokémon",
        "subtypes": "Basic",
        "image_small": "https://images.pokemontcg.io/base1/10.png",
        "image_large": "https://images.pokemontcg.io/base1/10_hires.png",
        "base_price": 120.0,
    },
    {
        "id": "swsh7-88",
        "name": "Umbreon VMAX",
        "set_name": "Evolving Skies",
        "set_code": "swsh7",
        "number": "88",
        "rarity": "Rare Rainbow",
        "supertype": "Pokémon",
        "subtypes": "VMAX",
        "image_small": "https://images.pokemontcg.io/swsh7/88.png",
        "image_large": "https://images.pokemontcg.io/swsh7/88_hires.png",
        "base_price": 85.0,
    },
    {
        "id": "sv3pt5-6",
        "name": "Charizard ex",
        "set_name": "151",
        "set_code": "sv3pt5",
        "number": "6",
        "rarity": "Double Rare",
        "supertype": "Pokémon",
        "subtypes": "ex,Basic",
        "image_small": "https://images.pokemontcg.io/sv3pt5/6.png",
        "image_large": "https://images.pokemontcg.io/sv3pt5/6_hires.png",
        "base_price": 45.0,
    },
    {
        "id": "swsh9-186",
        "name": "Arceus VSTAR",
        "set_name": "Brilliant Stars",
        "set_code": "swsh9",
        "number": "186",
        "rarity": "Rare Secret",
        "supertype": "Pokémon",
        "subtypes": "VSTAR",
        "image_small": "https://images.pokemontcg.io/swsh9/186.png",
        "image_large": "https://images.pokemontcg.io/swsh9/186_hires.png",
        "base_price": 28.0,
    },
    {
        "id": "xy1-12",
        "name": "Venusaur EX",
        "set_name": "XY",
        "set_code": "xy1",
        "number": "12",
        "rarity": "Rare Ultra",
        "supertype": "Pokémon",
        "subtypes": "EX,Basic",
        "image_small": "https://images.pokemontcg.io/xy1/12.png",
        "image_large": "https://images.pokemontcg.io/xy1/12_hires.png",
        "base_price": 18.0,
    },
    {
        "id": "swsh7-74",
        "name": "Sylveon VMAX",
        "set_name": "Evolving Skies",
        "set_code": "swsh7",
        "number": "74",
        "rarity": "Rare Ultra",
        "supertype": "Pokémon",
        "subtypes": "VMAX",
        "image_small": "https://images.pokemontcg.io/swsh7/74.png",
        "image_large": "https://images.pokemontcg.io/swsh7/74_hires.png",
        "base_price": 22.0,
    },
    {
        "id": "sv1-81",
        "name": "Miraidon ex",
        "set_name": "Scarlet & Violet",
        "set_code": "sv1",
        "number": "81",
        "rarity": "Double Rare",
        "supertype": "Pokémon",
        "subtypes": "ex,Basic",
        "image_small": "https://images.pokemontcg.io/sv1/81.png",
        "image_large": "https://images.pokemontcg.io/sv1/81_hires.png",
        "base_price": 32.0,
    },
    {
        "id": "base1-2",
        "name": "Blastoise",
        "set_name": "Base Set",
        "set_code": "base1",
        "number": "2",
        "rarity": "Rare Holo",
        "supertype": "Pokémon",
        "subtypes": "Stage 2",
        "image_small": "https://images.pokemontcg.io/base1/2.png",
        "image_large": "https://images.pokemontcg.io/base1/2_hires.png",
        "base_price": 95.0,
    },
]

# Market templates: (market_type, title_template, target_factor, days, signal, pool_yes, pool_no)
MARKET_TEMPLATES = [
    ("price_above", "Will {name} stay above ${target:.0f} in 7 days?", 0.95, 7, "price_spike", 1350, 850),
    ("new_high",    "Will {name} reach a new 30-day high in 72 hours?",  1.05, 3, "volume_spike", 920, 1280),
    ("price_above", "Will {name} hold above ${target:.0f} by end of week?", 0.90, 7, "trend_up", 1100, 1000),
    ("price_recovery", "Will {name} recover above ${target:.0f} in 7 days?", 1.02, 7, "price_crash", 780, 1420),
    ("price_above", "Will {name} stay above ${target:.0f} for 3 more days?", 0.98, 3, "price_spike", 1600, 600),
    ("new_high",    "Will {name} surpass ${target:.0f} within a week?", 1.10, 7, "volume_spike", 850, 1350),
    ("price_above", "Will {name} remain above ${target:.0f} through weekend?", 0.92, 5, "trend_up", 1200, 900),
    ("price_recovery", "Will {name} bounce back above ${target:.0f}?", 0.99, 7, "price_crash", 700, 1500),
    ("new_high",    "Will {name} hit ${target:.0f} before this market closes?", 1.08, 5, "volume_spike", 1050, 1150),
    ("price_above", "Will {name} end above ${target:.0f} next week?", 0.96, 7, "trend_up", 1400, 800),
]


def price_walk(base: float, days: int) -> list[float]:
    """Generate a realistic random walk price series."""
    prices = [base]
    for _ in range(days - 1):
        # Slight upward bias with daily volatility
        change = random.gauss(0.001, 0.025)
        new_price = prices[-1] * (1 + change)
        new_price = max(new_price, base * 0.3)  # floor at 30% of base
        prices.append(round(new_price, 2))
    return prices


async def main():
    # Import all models
    from app.models import user, subscription, wallet  # noqa: F401
    from app.models.card import Card
    from app.models.price import CardPrice
    from app.models.market import PredictionMarket
    from app.models.deal import DealListing
    from app.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        now = datetime.now(timezone.utc)

        # ----------------------------------------------------------------
        # 1. Upsert cards
        # ----------------------------------------------------------------
        print("Seeding cards...")
        for c in CARDS:
            stmt = sqlite_insert(Card).values(
                id=c["id"],
                name=c["name"],
                set_name=c["set_name"],
                set_code=c["set_code"],
                number=c["number"],
                rarity=c["rarity"],
                supertype=c["supertype"],
                subtypes=c["subtypes"],
                image_small=c["image_small"],
                image_large=c["image_large"],
                fetched_at=now,
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": c["name"],
                    "image_small": c["image_small"],
                    "image_large": c["image_large"],
                    "fetched_at": now,
                },
            )
            await db.execute(stmt)
        await db.flush()
        print(f"  {len(CARDS)} cards upserted.")

        # ----------------------------------------------------------------
        # 2. Price history — 90 days per card
        # ----------------------------------------------------------------
        print("Seeding price history (90 days × 10 cards)...")
        price_rows = 0
        card_final_prices: dict[str, float] = {}

        for c in CARDS:
            # Check if we already have lots of prices for this card
            existing = await db.execute(
                select(CardPrice).where(CardPrice.card_id == c["id"]).limit(5)
            )
            if existing.scalars().first() is not None:
                # Still compute the final price for market generation
                latest = await db.execute(
                    select(CardPrice)
                    .where(CardPrice.card_id == c["id"])
                    .order_by(CardPrice.recorded_at.desc())
                    .limit(1)
                )
                row = latest.scalar_one_or_none()
                card_final_prices[c["id"]] = row.price_usd if row else c["base_price"]
                continue

            prices = price_walk(c["base_price"], 90)
            card_final_prices[c["id"]] = prices[-1]

            for day_offset, price in enumerate(prices):
                recorded = now - timedelta(days=89 - day_offset)
                db.add(CardPrice(
                    card_id=c["id"],
                    source="tcgplayer",
                    price_type="market",
                    price_usd=price,
                    recorded_at=recorded,
                ))
                price_rows += 1

        await db.flush()
        print(f"  {price_rows} price snapshots inserted.")

        # ----------------------------------------------------------------
        # 3. Prediction markets — 10 markets
        # ----------------------------------------------------------------
        print("Seeding prediction markets...")
        existing_markets = await db.execute(
            select(PredictionMarket).where(PredictionMarket.status == "open").limit(1)
        )
        if existing_markets.scalars().first() is not None:
            print("  Markets already exist — skipping.")
        else:
            for i, (card, tmpl) in enumerate(zip(CARDS, MARKET_TEMPLATES)):
                mtype, title_tpl, factor, days, signal, pool_yes, pool_no = tmpl
                current_price = card_final_prices.get(card["id"], card["base_price"])
                target = round(current_price * factor, 2)
                title = title_tpl.format(name=card["name"], target=target)
                # Add some random variance to pools
                pool_yes += random.randint(-100, 200)
                pool_no  += random.randint(-100, 200)
                total_vol = pool_yes + pool_no - 2000  # approx wagered so far

                market = PredictionMarket(
                    title=title,
                    description=f"Auto-generated market based on recent {signal.replace('_',' ')} signal for {card['name']}.",
                    item_type="card",
                    card_id=card["id"],
                    market_type=mtype,
                    currency="coins",
                    target_value=target,
                    target_date=now + timedelta(days=days),
                    status="open",
                    pool_yes=float(pool_yes),
                    pool_no=float(pool_no),
                    total_volume=max(0.0, float(total_vol)),
                    trigger_signal=signal,
                )
                db.add(market)

            await db.flush()
            print(f"  {len(CARDS)} markets created.")

        # ----------------------------------------------------------------
        # 4. Deal listings — 5 active deals
        # ----------------------------------------------------------------
        print("Seeding deal listings...")
        existing_deals = await db.execute(
            select(DealListing).limit(1)
        )
        if existing_deals.scalars().first() is not None:
            print("  Deal listings already exist — skipping.")
        else:
            deal_cards = CARDS[:5]
            deal_scores = [42.0, 31.5, 27.0, 18.5, 12.0]
            conditions = ["Near Mint", "Near Mint", "Lightly Played", "Near Mint", "Moderately Played"]
            sellers = ["poke_vault_99", "tcg_deals_co", "rare_finds_usa", "mintcards", "bulk_breakers"]

            for idx, (card, score, condition, seller) in enumerate(zip(deal_cards, deal_scores, conditions, sellers)):
                market_price = card_final_prices.get(card["id"], card["base_price"])
                listed_price = round(market_price * (1 - score / 100), 2)
                db.add(DealListing(
                    item_type="card",
                    card_id=card["id"],
                    source="ebay",
                    external_id=f"ebay_demo_{idx + 1000}",
                    listing_url=f"https://www.ebay.com/itm/demo-listing-{idx + 1000}",
                    listed_price=listed_price,
                    market_price=round(market_price, 2),
                    deal_score=score,
                    condition=condition,
                    seller=seller,
                    status="active",
                    expires_at=now + timedelta(hours=24),
                ))

            await db.flush()
            print(f"  5 deal listings created.")

        await db.commit()
        print("\nSeed complete!")
        print("  Cards:   10")
        print("  Prices:  up to 900 snapshots (90 days × 10 cards)")
        print("  Markets: 10 open prediction markets")
        print("  Deals:   5 active eBay deal listings")


if __name__ == "__main__":
    asyncio.run(main())
