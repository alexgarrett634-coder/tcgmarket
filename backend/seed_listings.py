"""Seed demo marketplace listings for all cards with accurate prices + PSA grades.

- Runs ALTER TABLE to add grade/grading_company columns (idempotent)
- Prefers real TCGPlayer prices from tcgdex; falls back to rarity-based heuristic
- Heuristic applies era multiplier: vintage sets (Base Set, Fossil, etc.) price higher
- Creates raw (ungraded) listings and PSA-graded listings (grades 6-10)
- All assigned to the demo seller (demo@pokemarket.app, user id=1)

Usage:
  cd backend
  python seed_listings.py
"""
import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import engine, create_tables
from app.models.listing import Listing, SellerProfile
from app.models.card import Card
from app.models.price import CardPrice
from app.models.user import User

# ─── Heuristic pricing by rarity (used only when no real price exists) ────────
# Ranges reflect real 2025 Pokemon TCG market prices for modern sets.
# Era multipliers (below) scale these up for vintage sets.
RARITY_PRICES: list[tuple[list[str], tuple[float, float]]] = [
    (["Special Illustration Rare"],          (15.00, 120.00)),
    (["Hyper Rare"],                         (10.00,  75.00)),
    (["Rainbow Rare"],                       ( 8.00,  50.00)),
    (["Gold Rare", "Gold Ultra Rare"],       ( 7.00,  40.00)),
    (["Illustration Rare"],                  ( 5.00,  40.00)),
    (["Alt Art", "Alternate Art"],           (12.00, 100.00)),
    (["Secret Rare"],                        (10.00,  60.00)),
    (["Ultra Rare"],                         ( 6.00,  30.00)),
    (["Double Rare"],                        ( 0.75,  10.00)),
    (["VMAX"],                               ( 2.00,  20.00)),
    (["VSTAR"],                              ( 1.50,  15.00)),
    (["Full Art"],                           ( 4.00,  25.00)),
    (["Radiant Rare"],                       ( 1.50,  12.00)),
    (["Holo Rare V", "Rare Holo V"],        ( 1.00,   8.00)),
    (["Rare Holo", "Holo Rare"],            ( 0.50,   6.00)),
    (["Rare"],                               ( 0.35,   3.00)),
    (["Uncommon"],                           ( 0.10,   0.75)),
    (["Common"],                             ( 0.05,   0.30)),
]
DEFAULT_PRICE_RANGE = (0.15, 1.00)

# ─── Pokemon demand multipliers ───────────────────────────────────────────────
# Applied to Rare and above (base price ≥ $0.50) to reflect real collector demand.
# Source: 2025 TCGPlayer/PriceCharting market knowledge.
POKEMON_DEMAND: dict[str, float] = {
    # Tier 1 — Trophy/Chase cards (5–8x premium over average card of same rarity)
    "charizard":   6.0,   # Base Set holo ~$250-400; modern SIR/Alt Art ~$50-200
    "lugia":       5.0,   # Neo Genesis holo ~$300; VSTAR ~$60-120
    "umbreon":     4.5,   # VMAX Alt Art ~$250-400; VSTAR ~$60
    "pikachu":     3.0,   # Lots of special arts; base set promo variants
    "mewtwo":      4.0,   # Base Set holo ~$60; VSTAR Alt Art ~$100
    "rayquaza":    4.0,   # VMAX Alt Art ~$150; Gold Star vintage
    "giratina":    3.5,   # VSTAR Alt Art ~$180
    "mew":         3.0,   # VMAX Alt Art ~$180; base set jungle holo
    # Tier 2 — Very popular (2.5–4x premium)
    "espeon":      3.0,   # VMAX Alt Art ~$120
    "blastoise":   3.0,   # Base Set holo ~$80-120
    "ho-oh":       3.0,   # Gold Star; Neo era
    "gengar":      2.5,   # Multiple popular prints
    "venusaur":    2.5,   # Base Set holo ~$60-100
    "celebi":      2.5,   # Neo Revelation/Destiny
    "arceus":      2.5,   # VSTAR/Legends prints
    "gyarados":    2.5,   # Base Set holo; multiple popular arts
    "darkrai":     2.5,   # Multiple popular prints
    # Tier 3 — Popular (1.5–2.5x premium)
    "eevee":       2.0,
    "sylveon":     2.0,
    "gardevoir":   2.0,   # ex SV very popular
    "alakazam":    2.0,   # Base Set holo
    "snorlax":     1.8,
    "dragonite":   1.8,
    "chansey":     1.8,   # Base Set holo
    "raichu":      1.8,   # Base Set holo; numerous arts
    "ninetales":   1.8,   # Base Set holo
    "kyogre":      1.8,
    "groudon":     1.8,
    "dialga":      1.8,
    "palkia":      1.8,
    "reshiram":    1.8,
    "zekrom":      1.8,
    "zapdos":      1.6,
    "moltres":     1.6,
    "articuno":    1.6,
    "tyranitar":   1.6,
    "lapras":      1.5,
    "machamp":     1.5,   # Base Set holo
    "nidoking":    1.5,
    "clefairy":    1.5,
}


def _name_multiplier(name: str | None) -> float:
    """Return demand multiplier for a card based on the Pokemon's popularity."""
    if not name:
        return 1.0
    n = name.lower()
    for pokemon, mult in POKEMON_DEMAND.items():
        if pokemon in n:
            return mult
    return 1.0


# ─── Era multipliers ──────────────────────────────────────────────────────────
# Vintage cards command significant premiums over modern equivalents.
_WOTC_BASE_ERA = frozenset({"base1", "jungle", "base2", "base3"})
_WOTC_OTHER = frozenset({
    "base4", "base5", "gym1", "gym2",
    "neo1", "neo2", "neo3", "neo4",
    "lc", "ecard1", "ecard2", "ecard3",
})


def _era_multiplier(set_code: str | None) -> float:
    if not set_code:
        return 1.0
    sc = set_code.lower()
    if sc in _WOTC_BASE_ERA:
        return random.uniform(8.0, 30.0)   # Base Set / Jungle / Fossil — very collectible
    if sc in _WOTC_OTHER:
        return random.uniform(2.0, 10.0)   # Other WOTC era
    if sc.startswith("ex"):
        return random.uniform(1.5,  4.0)   # EX era (2003-2007)
    if sc[:2] in {"dp", "pl"} or sc.startswith("hgss") or sc in {"col1"}:
        return random.uniform(1.2,  2.5)   # Diamond/Pearl / Platinum / HGSS
    if sc.startswith("bw"):
        return random.uniform(1.0,  1.8)   # Black & White era
    return 1.0                              # Modern: XY / SM / SWSH / SV


def get_heuristic_price(rarity: str | None, set_code: str | None = None, name: str | None = None) -> float:
    """Return a heuristic market price based on rarity + era + pokemon demand."""
    if rarity:
        r_lower = rarity.lower()
        for keywords, (lo, hi) in RARITY_PRICES:
            if any(k.lower() in r_lower for k in keywords):
                base = random.uniform(lo, hi)
                era = _era_multiplier(set_code)
                # Apply name demand multiplier for cards worth at least $0.50 baseline
                demand = _name_multiplier(name) if base >= 0.50 else 1.0
                return round(max(0.05, base * era * demand), 2)
    lo, hi = DEFAULT_PRICE_RANGE
    base = random.uniform(lo, hi)
    return round(max(0.05, base * _era_multiplier(set_code)), 2)


PSA_GRADES = [6, 7, 8, 9, 10]
PSA_MULTIPLIERS = {
    10: (3.5, 6.0),
    9:  (1.8, 2.5),
    8:  (1.3, 1.7),
    7:  (1.1, 1.3),
    6:  (0.85, 1.05),
}
# PSA slab + authentication adds a hard floor to every graded card regardless of raw value.
# PSA 10 certification alone implies premium; lower grades still carry the slab cost.
PSA_FLOOR = {
    10: 30.00,
    9:  18.00,
    8:  14.00,
    7:  10.00,
    6:   8.00,
}

CONDITION_DISCOUNT = {"NM": 1.00, "LP": 0.88, "MP": 0.70}


async def seed():
    await create_tables()

    # Add grade columns via ALTER TABLE (idempotent — ignore error if column exists)
    async with engine.begin() as conn:
        for col_def in ["grade INTEGER", "grading_company TEXT"]:
            col_name = col_def.split()[0]
            try:
                await conn.execute(text(f"ALTER TABLE listings ADD COLUMN {col_def}"))
                print(f"Added column: {col_name}")
            except Exception:
                pass  # Column already exists

    async with AsyncSession(engine, expire_on_commit=False) as db:
        # Verify demo seller exists
        result = await db.execute(select(User).where(User.email == "demo@pokemarket.app"))
        seller = result.scalar_one_or_none()
        if not seller:
            print("ERROR: No demo@pokemarket.app user found.")
            return

        sp_result = await db.execute(
            select(SellerProfile).where(SellerProfile.user_id == seller.id)
        )
        sp = sp_result.scalar_one_or_none()
        if not sp or not sp.onboarding_complete:
            print("ERROR: Demo user has no completed seller profile.")
            return

        # Cancel existing demo card listings (sealed listings are managed by seed_products.py)
        existing = await db.execute(
            select(Listing).where(
                Listing.seller_id == seller.id,
                Listing.status == "active",
                Listing.item_type == "card",
            )
        )
        cancelled = 0
        for lst in existing.scalars().all():
            lst.status = "cancelled"
            cancelled += 1
        await db.commit()
        print(f"Cancelled {cancelled} existing listings.")

        # Get all cards
        card_result = await db.execute(select(Card))
        all_cards = card_result.scalars().all()
        print(f"Found {len(all_cards)} cards.")

        # ── Load prices: pricecharting > tcgplayer > heuristic ──────────────
        # Three-pass: first real PriceCharting data, then tcgplayer, heuristic last.
        # setdefault() ensures higher-priority sources are never overridden.
        known_prices: dict[str, float] = {}
        # Also load PSA grade-specific prices from PriceCharting (psa6..psa10)
        psa_prices: dict[str, dict[int, float]] = {}  # card_id → {grade: price}

        for source in ("pricecharting", "tcgplayer", "heuristic"):
            pr = await db.execute(
                select(CardPrice.card_id, CardPrice.price_usd, CardPrice.price_type)
                .where(CardPrice.source == source)
                .order_by(CardPrice.recorded_at.desc())
            )
            for card_id, price, price_type in pr.all():
                if price_type == "market":
                    known_prices.setdefault(card_id, price)
                elif price_type.startswith("psa") and price_type[3:].isdigit():
                    grade = int(price_type[3:])
                    psa_prices.setdefault(card_id, {}).setdefault(grade, price)

        pc_count = sum(1 for _ in known_prices)  # rough; sources overlap
        print(f"Loaded {len(known_prices):,} existing prices ({len(psa_prices):,} with PSA grade data).")

        now = datetime.now(timezone.utc)
        new_prices = 0
        listings_created = 0
        batch_size = 500

        for batch_start in range(0, len(all_cards), batch_size):
            batch = all_cards[batch_start:batch_start + batch_size]

            for card in batch:
                # Get or generate market price (NM baseline)
                if card.id in known_prices:
                    nm_price = known_prices[card.id]
                else:
                    nm_price = get_heuristic_price(card.rarity, card.set_code, card.name)
                    known_prices[card.id] = nm_price
                    db.add(CardPrice(
                        card_id=card.id,
                        source="heuristic",
                        price_type="market",
                        price_usd=nm_price,
                        recorded_at=now,
                    ))
                    new_prices += 1

                # --- Raw (ungraded) listings ---
                conditions = ["NM"]
                if nm_price >= 1.00:
                    conditions.append("LP")
                if nm_price >= 10.00:
                    conditions.append("MP")

                for condition in conditions:
                    disc = CONDITION_DISCOUNT[condition]
                    variation = random.uniform(0.93, 1.07)
                    price = round(max(0.05, nm_price * disc * variation), 2)
                    qty = random.choice([1, 1, 2, 3]) if nm_price < 5 else 1

                    db.add(Listing(
                        seller_id=seller.id,
                        item_type="card",
                        card_id=card.id,
                        title=f"{card.name} - {condition}",
                        condition=condition,
                        quantity=qty,
                        price=price,
                        status="active",
                        grade=None,
                        grading_company=None,
                    ))
                    listings_created += 1

                # --- Motivated-seller deal listing (~20% of cards ≥ $1.00) ---
                # These are priced 20-35% below NM, guaranteeing they appear in the Deals tab.
                if nm_price >= 1.00 and random.random() < 0.20:
                    sale_disc = random.uniform(0.65, 0.80)
                    sale_price = round(max(0.05, nm_price * sale_disc), 2)
                    db.add(Listing(
                        seller_id=seller.id,
                        item_type="card",
                        card_id=card.id,
                        title=f"{card.name} - Sale",
                        condition="NM",
                        quantity=random.randint(1, 2),
                        price=sale_price,
                        status="active",
                        grade=None,
                        grading_company=None,
                    ))
                    listings_created += 1

                # --- PSA graded listings ---
                # Only list PSA grades for cards valuable enough to realistically be submitted.
                # PSA grading costs $18–50/card, so low-value cards are never professionally graded.
                if nm_price >= 30.00:
                    grades_to_add = PSA_GRADES        # all grades 6-10
                elif nm_price >= 15.00:
                    grades_to_add = [8, 9, 10]
                elif nm_price >= 5.00:
                    grades_to_add = [9, 10]
                else:
                    grades_to_add = []

                for grade in grades_to_add:
                    # Use real PriceCharting PSA price if available
                    pc_psa = psa_prices.get(card.id, {}).get(grade)
                    if pc_psa and pc_psa >= PSA_FLOOR[grade]:
                        psa_price = round(pc_psa * random.uniform(0.97, 1.03), 2)  # ±3% spread
                    else:
                        lo_mult, hi_mult = PSA_MULTIPLIERS[grade]
                        floor = PSA_FLOOR[grade]
                        psa_price = round(max(floor, nm_price * random.uniform(lo_mult, hi_mult)), 2)

                    psa_condition = "GEM MT" if grade == 10 else "NM"
                    db.add(Listing(
                        seller_id=seller.id,
                        item_type="card",
                        card_id=card.id,
                        title=f"{card.name} - PSA {grade}",
                        condition=psa_condition,
                        quantity=1,
                        price=psa_price,
                        status="active",
                        grade=grade,
                        grading_company="PSA",
                    ))
                    listings_created += 1

            await db.commit()
            pct = min(100, int((batch_start + len(batch)) / len(all_cards) * 100))
            print(f"  {batch_start + len(batch)}/{len(all_cards)} cards ({pct}%) — {listings_created:,} listings")

        print(f"\nDone!")
        print(f"  New heuristic prices generated: {new_prices:,}")
        print(f"  Total listings created: {listings_created:,}")


if __name__ == "__main__":
    asyncio.run(seed())
