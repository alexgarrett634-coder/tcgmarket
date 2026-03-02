from .base import fetch_with_retry

TCGDEX_BASE = "https://api.tcgdex.net/v2/en"
TTL_HOURS = 4.0


async def fetch_card_prices(set_code: str, card_number: str) -> list[dict]:
    data = await fetch_with_retry(f"{TCGDEX_BASE}/sets/{set_code}/{card_number}")
    if not data:
        return []

    prices = data.get("prices", {})
    results = []

    tcgp = prices.get("tcgplayer", {})
    for price_type, field_name in [
        ("market", "normal"),
        ("holofoil", "holofoil"),
        ("reverse_holofoil", "reverseHolofoil"),
    ]:
        val = tcgp.get(field_name)
        if val is not None:
            results.append({"source": "tcgplayer", "price_type": price_type, "price_usd": float(val)})

    cm = prices.get("cardmarket", {})
    for price_type, field_name in [
        ("market", "averageSellPrice"),
        ("low", "lowPrice"),
    ]:
        val = cm.get(field_name)
        if val is not None:
            results.append({"source": "cardmarket", "price_type": price_type, "price_usd": float(val)})

    return results
