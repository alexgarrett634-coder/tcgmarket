from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.market import PredictionMarket, MarketPosition
from app.models.wallet import Wallet, WalletTransaction
from app.models.notification import Notification
from app.services.price_service import get_latest_price
from app.config import settings


def buy_shares(pool_yes: float, pool_no: float, side: str, amount: float) -> tuple[float, float, float]:
    """FPMM: returns (shares_received, new_pool_yes, new_pool_no)."""
    k = pool_yes * pool_no
    if side == "yes":
        new_pool_no = pool_no + amount
        new_pool_yes = k / new_pool_no
        shares = pool_yes - new_pool_yes
    else:
        new_pool_yes = pool_yes + amount
        new_pool_no = k / new_pool_yes
        shares = pool_no - new_pool_no
    return shares, new_pool_yes, new_pool_no


def get_probability(pool_yes: float, pool_no: float) -> float:
    return pool_no / (pool_yes + pool_no)


async def place_position(
    db: AsyncSession,
    user_id: int,
    market_id: int,
    side: str,
    amount: float,
) -> dict:
    """Deduct wallet balance, update market pools, create position + transaction."""
    # Load market
    market = await db.get(PredictionMarket, market_id)
    if not market:
        raise HTTPException(404, "Market not found")
    if market.status != "open":
        raise HTTPException(400, "Market is not open")
    if side not in ("yes", "no"):
        raise HTTPException(400, "side must be 'yes' or 'no'")
    if amount <= 0:
        raise HTTPException(400, "amount must be positive")

    # Load wallet
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(400, "Wallet not found")

    # Deduct from correct balance
    if market.currency == "coins":
        if wallet.prediction_coins < int(amount):
            raise HTTPException(400, "Insufficient Prediction Coins")
        wallet.prediction_coins -= int(amount)
    else:
        if wallet.real_credits_usd < amount:
            raise HTTPException(400, "Insufficient Market Credits")
        wallet.real_credits_usd -= amount
    wallet.updated_at = datetime.now(timezone.utc)

    # FPMM calculation
    shares, new_pool_yes, new_pool_no = buy_shares(market.pool_yes, market.pool_no, side, amount)
    market.pool_yes = new_pool_yes
    market.pool_no = new_pool_no
    market.total_volume += amount

    # Create position
    position = MarketPosition(
        user_id=user_id,
        market_id=market_id,
        side=side,
        shares=shares,
        cost=amount,
        currency=market.currency,
    )
    db.add(position)

    # Transaction log
    db.add(WalletTransaction(
        user_id=user_id,
        type="market_buy",
        currency=market.currency,
        amount=-amount,
        market_id=market_id,
        note=f"Bought {shares:.4f} {side.upper()} shares in market #{market_id}",
    ))

    await db.flush()
    return {
        "shares": shares,
        "probability": get_probability(new_pool_yes, new_pool_no),
        "position_id": position.id,
    }


async def resolve_market(db: AsyncSession, market: PredictionMarket) -> None:
    """Fetch final price, determine outcome, settle positions, send notifications."""
    if market.status != "open":
        return

    # Fetch current price as resolved price
    final_price: float | None = None
    if market.card_id:
        final_price = await get_latest_price(db, market.card_id, source="tcgplayer")
    if final_price is None:
        # Can't resolve yet — no price data
        return

    market.resolved_price = final_price
    market.resolved_at = datetime.now(timezone.utc)

    # Determine outcome based on market_type
    if market.market_type in ("price_above", "new_high"):
        outcome = "yes" if final_price >= (market.target_value or 0) else "no"
    else:
        outcome = "yes" if final_price >= (market.target_value or 0) else "no"

    market.resolved_outcome = outcome
    market.status = "resolved"

    # Settle positions
    result = await db.execute(
        select(MarketPosition).where(
            MarketPosition.market_id == market.id,
            MarketPosition.settled == False,
        )
    )
    positions = result.scalars().all()

    for pos in positions:
        pos.settled = True
        pos.settled_at = datetime.now(timezone.utc)

        if pos.side == outcome:
            # Winner: 1 coin/credit per share
            payout = pos.shares
            pos.payout = payout

            # Credit wallet
            wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == pos.user_id))
            wallet = wallet_res.scalar_one_or_none()
            if wallet:
                if pos.currency == "coins":
                    wallet.prediction_coins += int(payout)
                else:
                    wallet.real_credits_usd += payout
                wallet.updated_at = datetime.now(timezone.utc)

            db.add(WalletTransaction(
                user_id=pos.user_id,
                type="market_payout",
                currency=pos.currency,
                amount=payout,
                market_id=market.id,
                note=f"Won {payout:.2f} from market #{market.id}",
            ))
            db.add(Notification(
                user_id=pos.user_id,
                type="market_won",
                title="You won!",
                message=f'Your {outcome.upper()} position on "{market.title}" paid out {payout:.2f}.',
                link=f"/markets/{market.id}",
            ))
        else:
            pos.payout = 0.0
            db.add(Notification(
                user_id=pos.user_id,
                type="market_lost",
                title="Market resolved",
                message=f'Your {pos.side.upper()} position on "{market.title}" did not win.',
                link=f"/markets/{market.id}",
            ))


async def get_market_detail(db: AsyncSession, market_id: int) -> dict:
    market = await db.get(PredictionMarket, market_id)
    if not market:
        raise HTTPException(404, "Market not found")
    return {
        "id": market.id,
        "title": market.title,
        "description": market.description,
        "item_type": market.item_type,
        "card_id": market.card_id,
        "product_id": market.product_id,
        "market_type": market.market_type,
        "currency": market.currency,
        "target_value": market.target_value,
        "target_date": market.target_date.isoformat(),
        "status": market.status,
        "resolved_outcome": market.resolved_outcome,
        "resolved_price": market.resolved_price,
        "probability": get_probability(market.pool_yes, market.pool_no),
        "pool_yes": market.pool_yes,
        "pool_no": market.pool_no,
        "total_volume": market.total_volume,
        "created_at": market.created_at.isoformat(),
        "trigger_signal": market.trigger_signal,
    }
