"""
Import One Piece TCG cards and prices from PriceCharting price-guide CSV into the DB.

Uses language="op" to distinguish One Piece cards in the shared cards table.
Card IDs are prefixed "op-{pricecharting_id}".

Price mapping:
  loose-price  → source="pricecharting", price_type="market"
  new-price    → source="pricecharting", price_type="near_mint"
  graded-price → source="pricecharting", price_type="graded"
  bgs-10-price → source="pricecharting", price_type="psa10"

Usage:
    cd backend
    python import_onepiece.py [/path/to/price-guide.csv]
"""

import asyncio
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal, create_tables, engine
from app.models.card import Card
from app.models.price import CardPrice

CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "C:/Users/Alex/Downloads/price-guide (2).csv"
)

# English One Piece genres only
OP_GENRES = {"One Piece Card", "One Piece Cards"}


def parse_card_name_and_code(product_name: str) -> tuple[str, str]:
    """
    Split 'Ain OP07-002' into ('Ain', 'OP07-002').
    The set code is the last token matching patterns like OP07-002, ST01-001, EB01-001.
    """
    tokens = product_name.strip().split()
    if not tokens:
        return product_name.strip(), ""
    last = tokens[-1]
    # One Piece codes: OP07-002, ST01-001, EB01-001, PRB01-001, etc.
    if re.match(r'^[A-Z]{2,5}\d{2,3}-\d+$', last, re.IGNORECASE):
        name = " ".join(tokens[:-1]).strip() or product_name.strip()
        return name, last.upper()
    return product_name.strip(), ""


def parse_price(raw: str) -> float | None:
    cleaned = raw.strip().lstrip("$").replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


async def run_import() -> None:
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        sys.exit(1)

    print(f"Loading CSV: {CSV_PATH.name}")
    await create_tables()
    now = datetime.utcnow()

    card_rows: list[dict] = []
    price_rows: list[dict] = []
    baseline_rows: list[dict] = []
    skipped_bracket = skipped_no_price = skipped_not_op = 0
    imported_cards: set[str] = set()

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            genre = row.get("genre", "")
            product_name = row.get("product-name", "").strip()
            console_name = row.get("console-name", "").strip()

            if genre not in OP_GENRES:
                skipped_not_op += 1
                continue

            # Skip variants (e.g. "[Alternate Art]", "[Pre-Release]")
            if "[" in product_name:
                skipped_bracket += 1
                continue

            loose = parse_price(row.get("loose-price", ""))
            if loose is None:
                skipped_no_price += 1
                continue

            pc_id = row.get("id", "").strip()
            card_id = f"op-{pc_id}"
            set_name = console_name  # e.g. "One Piece 500 Years in the Future"
            card_name, set_code = parse_card_name_and_code(product_name)

            new_p  = parse_price(row.get("new-price", ""))
            graded = parse_price(row.get("graded-price", ""))
            bgs10  = parse_price(row.get("bgs-10-price", ""))

            if card_id not in imported_cards:
                imported_cards.add(card_id)
                card_rows.append({
                    "id": card_id,
                    "name": card_name,
                    "set_name": set_name,
                    "set_code": set_code or set_name[:20],
                    "number": set_code or None,
                    "rarity": None,
                    "supertype": "Card",
                    "subtypes": None,
                    "image_small": None,
                    "image_large": None,
                    "language": "op",
                    "fetched_at": now,
                })

            price_rows.append({
                "card_id": card_id, "source": "pricecharting",
                "price_type": "market", "price_usd": loose, "recorded_at": now,
            })
            baseline_rows.append({
                "card_id": card_id, "source": "tcgplayer",
                "price_type": "market", "price_usd": loose, "recorded_at": now,
            })
            if new_p is not None:
                price_rows.append({
                    "card_id": card_id, "source": "pricecharting",
                    "price_type": "near_mint", "price_usd": new_p, "recorded_at": now,
                })
            if graded is not None:
                price_rows.append({
                    "card_id": card_id, "source": "pricecharting",
                    "price_type": "graded", "price_usd": graded, "recorded_at": now,
                })
            if bgs10 is not None:
                price_rows.append({
                    "card_id": card_id, "source": "pricecharting",
                    "price_type": "psa10", "price_usd": bgs10, "recorded_at": now,
                })

    print(f"\nCSV parse results:")
    print(f"  Unique One Piece cards:  {len(card_rows):,}")
    print(f"  Price rows:              {len(price_rows):,}")
    print(f"  Tcgplayer baseline:      {len(baseline_rows):,}")
    print(f"  Skipped (not OP):        {skipped_not_op:,}")
    print(f"  Skipped (variants):      {skipped_bracket:,}")
    print(f"  Skipped (no price):      {skipped_no_price:,}")

    if not card_rows:
        print("Nothing to import.")
        return

    print("\nWriting to database...")
    async with AsyncSessionLocal() as db:
        del_cards = await db.execute(
            text("DELETE FROM cards WHERE language = 'op'")
        )
        print(f"  Deleted {del_cards.rowcount:,} old One Piece card rows")

        del_prices = await db.execute(
            text("DELETE FROM card_prices WHERE card_id LIKE 'op-%'")
        )
        print(f"  Deleted {del_prices.rowcount:,} old One Piece price rows")

        inserted_cards = 0
        for i in range(0, len(card_rows), 500):
            chunk = card_rows[i: i + 500]
            db.add_all([Card(**r) for r in chunk])
            inserted_cards += len(chunk)

        all_price_rows = price_rows + baseline_rows
        inserted_prices = 0
        for i in range(0, len(all_price_rows), 500):
            chunk = all_price_rows[i: i + 500]
            db.add_all([CardPrice(**r) for r in chunk])
            inserted_prices += len(chunk)
            if inserted_prices % 5000 == 0 or inserted_prices == len(all_price_rows):
                print(f"  Prices: {inserted_prices:,} / {len(all_price_rows):,}...", end="\r")

        await db.commit()

    print(f"\nDone!")
    print(f"  {inserted_cards:,} One Piece cards imported")
    print(f"  {len(price_rows):,} pricecharting price rows")
    print(f"  {len(baseline_rows):,} tcgplayer baseline rows")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_import())
