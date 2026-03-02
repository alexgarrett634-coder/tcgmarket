from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_each: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.06, nullable=False)
    commission_amount: Mapped[float] = mapped_column(Float, nullable=False)
    payout_amount: Mapped[float] = mapped_column(Float, nullable=False)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_transfer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # pending → paid → shipped → completed / cancelled
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON blob
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
    listing: Mapped["Listing"] = relationship("Listing")
