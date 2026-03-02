from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from typing import Optional
import json

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.order import Order
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


def _fmt(order: Order) -> dict:
    return {
        "id": order.id,
        "buyer_id": order.buyer_id,
        "seller_id": order.seller_id,
        "listing_id": order.listing_id,
        "quantity": order.quantity,
        "price_each": order.price_each,
        "subtotal": order.subtotal,
        "commission_rate": order.commission_rate,
        "commission_amount": order.commission_amount,
        "payout_amount": order.payout_amount,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "shipping_address": json.loads(order.shipping_address) if order.shipping_address else None,
        "created_at": order.created_at.isoformat(),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
    }


class CreateOrderRequest(BaseModel):
    listing_id: int
    quantity: int = 1
    shipping_address: dict


@router.post("", status_code=201)
async def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await order_service.create_order(
        db,
        buyer_id=current_user.id,
        listing_id=body.listing_id,
        quantity=body.quantity,
        shipping_address=body.shipping_address,
    )
    return result


@router.get("")
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Buyer: get orders where I am the buyer."""
    result = await db.execute(
        select(Order)
        .where(Order.buyer_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [_fmt(o) for o in orders]


@router.get("/selling")
async def get_selling_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seller: get orders where I am the seller."""
    result = await db.execute(
        select(Order)
        .where(Order.seller_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [_fmt(o) for o in orders]


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "Not your order")
    return _fmt(order)


class ShipRequest(BaseModel):
    tracking_number: str


@router.post("/{order_id}/ship")
async def ship_order(
    order_id: int,
    body: ShipRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.mark_shipped(db, order_id, current_user.id, body.tracking_number)
    return _fmt(order)


@router.post("/{order_id}/complete")
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.mark_completed(db, order_id, current_user.id)
    return _fmt(order)
