"""Insights service: eBay-based price predictions for TCG cards."""
import statistics
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.fetchers import ebay


async def predict_card_value(db: AsyncSession, card_id: str) -> dict:
    card = await db.get(Card, card_id)
    if not card:
        return {"error": "Card not found"}

    # Fetch active eBay listings for this card
    query = f"{card.name} {card.set_name} pokemon card" if card.language == "en" else f"{card.name} card"
    listings = await ebay.search_listings(query, limit=10)
    if not listings:
        return {"error": "No eBay data available for this card"}

    prices = [l["price"] for l in listings]
    current_ebay = statistics.median(prices)

    # Apply release-period depreciation for new cards (within 60-day window)
    predicted = current_ebay
    days_since_release = None
    new_release = False

    if card.set_release_date:
        days_since_release = (date.today() - card.set_release_date).days
        if days_since_release < 60:
            new_release = True
            # Linear decay: up to 30% at day 0, decaying to 0% at day 60
            decay = 0.30 * (1 - days_since_release / 60)
            predicted = current_ebay * (1 - decay)

    change_pct = round((predicted - current_ebay) / current_ebay * 100, 1) if current_ebay else 0

    return {
        "card_id": card_id,
        "card_name": card.name,
        "set_name": card.set_name,
        "current_ebay_median": round(current_ebay, 2),
        "predicted_2mo_value": round(predicted, 2),
        "change_pct": change_pct,
        "days_since_release": days_since_release,
        "new_release": new_release,
        "ebay_sample_size": len(prices),
        "ebay_price_range": {"min": round(min(prices), 2), "max": round(max(prices), 2)},
    }
