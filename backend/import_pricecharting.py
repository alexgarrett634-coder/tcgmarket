"""
Import PriceCharting price-guide.csv into the pokemon-price-tracker database.

Matches CSV rows to existing cards by (set_name, card_number) using both exact
and normalized set-name matching (handles em-dashes, spacing differences, etc.).

Also resets the tcgplayer market-price baseline for every matched card so the
per-minute scheduler job starts its random walk from correct real-world values.

Usage:
    cd backend
    python import_pricecharting.py [/path/to/price-guide.csv]
"""

import asyncio
import csv
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete, select, text
from app.database import AsyncSessionLocal, create_tables, engine
from app.models.price import CardPrice

CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "C:/Users/Alex/Downloads/price-guide.csv"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_set(name: str) -> str:
    """Normalize set name for fuzzy comparison.

    Handles em-dashes (Scarlet & Violet—151 → scarlet & violet 151),
    extra whitespace, and Unicode quirks.
    """
    name = unicodedata.normalize('NFKD', name)
    name = name.replace('\u2014', ' ').replace('\u2013', ' ')  # em/en dash → space
    name = name.replace('\u2019', "'")                          # curly apostrophe
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def parse_price(raw: str) -> float | None:
    """Strip '$' and commas, return float or None."""
    cleaned = raw.strip().lstrip('$').replace(',', '')
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_number(product_name: str) -> str | None:
    """Extract card number: 'Charizard #4' → '4'."""
    if '#' not in product_name:
        return None
    return product_name.split('#')[-1].strip()


def parse_set_name(console_name: str) -> str:
    """Strip 'Pokemon ' prefix."""
    if console_name.startswith('Pokemon '):
        return console_name[len('Pokemon '):]
    return console_name


# ---------------------------------------------------------------------------
# Build card lookup from DB
# ---------------------------------------------------------------------------

async def load_card_lookup() -> tuple[dict, dict]:
    """
    Returns two dicts:
      exact_lookup:  {(set_name, number): card_id}
      normal_lookup: {(normalize_set(set_name), number): card_id}
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(text('id'), text('set_name'), text('number'))
            .select_from(text('cards'))
            .where(text('number IS NOT NULL'))
        )
        rows = result.all()

    exact: dict[tuple[str, str], str] = {}
    normal: dict[tuple[str, str], str] = {}

    for card_id, set_name, number in rows:
        if not set_name or not number:
            continue
        sn = set_name.strip()
        num = number.strip()
        exact[(sn, num)] = card_id
        nkey = (normalize_set(sn), num)
        if nkey not in normal:          # prefer first occurrence
            normal[nkey] = card_id

    return exact, normal


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_import() -> None:
    if not CSV_PATH.exists():
        print(f'ERROR: CSV not found at {CSV_PATH}')
        sys.exit(1)

    print('Loading cards from database...')
    await create_tables()
    exact_lookup, normal_lookup = await load_card_lookup()
    total_db_cards = len(exact_lookup)
    print(f'  {total_db_cards:,} cards loaded ({len(normal_lookup):,} normalized keys)')

    now = datetime.now(timezone.utc)

    # price_rows: list of dicts for CardPrice inserts
    price_rows: list[dict] = []
    # tcgplayer baseline: one market row per matched card
    baseline_rows: list[dict] = []
    # track which card_ids we matched (for deleting old tcgplayer records)
    matched_card_ids: set[str] = set()

    matched = skipped_variant = skipped_no_number = unmatched = 0
    matched_exact = matched_norm = 0

    print(f'Parsing {CSV_PATH.name}...')
    with open(CSV_PATH, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_name = row['product-name']
            console_name = row['console-name']

            # Skip edition/variant entries (e.g. "Charizard [1st Edition] #4")
            if '[' in product_name:
                skipped_variant += 1
                continue

            number = parse_number(product_name)
            if number is None:
                skipped_no_number += 1
                continue

            set_name = parse_set_name(console_name)

            # 1. Try exact match
            card_id = exact_lookup.get((set_name, number))
            if card_id:
                matched_exact += 1
            else:
                # 2. Try normalized match
                card_id = normal_lookup.get((normalize_set(set_name), number))
                if card_id:
                    matched_norm += 1

            if card_id is None:
                unmatched += 1
                continue

            matched += 1
            matched_card_ids.add(card_id)

            loose  = parse_price(row.get('loose-price', ''))
            new_p  = parse_price(row.get('new-price', ''))
            graded = parse_price(row.get('graded-price', ''))
            bgs10  = parse_price(row.get('bgs-10-price', ''))

            if loose is not None:
                price_rows.append({
                    'card_id': card_id, 'source': 'pricecharting',
                    'price_type': 'market', 'price_usd': loose, 'recorded_at': now,
                })
                # Reset tcgplayer baseline to match real market price
                baseline_rows.append({
                    'card_id': card_id, 'source': 'tcgplayer',
                    'price_type': 'market', 'price_usd': loose, 'recorded_at': now,
                })
            if new_p is not None:
                price_rows.append({
                    'card_id': card_id, 'source': 'pricecharting',
                    'price_type': 'near_mint', 'price_usd': new_p, 'recorded_at': now,
                })
            if graded is not None:
                price_rows.append({
                    'card_id': card_id, 'source': 'pricecharting',
                    'price_type': 'graded', 'price_usd': graded, 'recorded_at': now,
                })
            if bgs10 is not None:
                price_rows.append({
                    'card_id': card_id, 'source': 'pricecharting',
                    'price_type': 'psa10', 'price_usd': bgs10, 'recorded_at': now,
                })

    print(f'\nCSV parse results:')
    print(f'  Matched (exact):    {matched_exact:,}')
    print(f'  Matched (fuzzy):    {matched_norm:,}')
    print(f'  Total matched:      {matched:,}')
    print(f'  Unmatched:          {unmatched:,}')
    print(f'  Skipped (variants): {skipped_variant:,}')
    print(f'  Skipped (no #):     {skipped_no_number:,}')
    print(f'  Price rows to insert: {len(price_rows):,}')
    print(f'  Tcgplayer baseline rows: {len(baseline_rows):,}')

    if not price_rows:
        print('Nothing to import. Exiting.')
        return

    all_rows = price_rows + baseline_rows

    print('\nWriting to database...')
    async with AsyncSessionLocal() as db:
        # Delete ALL existing pricecharting records
        del1 = await db.execute(
            delete(CardPrice).where(CardPrice.source == 'pricecharting')
        )
        print(f'  Deleted {del1.rowcount:,} old pricecharting rows')

        # Delete stale tcgplayer records for matched cards so wrong seed values
        # don't linger in the 24-hour window alongside the new correct baseline
        if matched_card_ids:
            del2 = await db.execute(
                delete(CardPrice).where(
                    CardPrice.source == 'tcgplayer',
                    CardPrice.price_type == 'market',
                    CardPrice.card_id.in_(list(matched_card_ids)),
                )
            )
            print(f'  Deleted {del2.rowcount:,} stale tcgplayer market rows for matched cards')

        # Bulk insert in chunks of 500
        inserted = 0
        for i in range(0, len(all_rows), 500):
            chunk = all_rows[i: i + 500]
            db.add_all([CardPrice(**r) for r in chunk])
            inserted += len(chunk)
            if inserted % 5000 == 0 or inserted == len(all_rows):
                print(f'  Inserted {inserted:,} / {len(all_rows):,}...', end='\r')

        await db.commit()

    print(f'\nDone!')
    print(f'  {len(price_rows):,} pricecharting price rows')
    print(f'  {len(baseline_rows):,} tcgplayer baseline rows (scheduler now walks from real prices)')
    print(f'  {matched:,} cards have real PriceCharting data')
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(run_import())
