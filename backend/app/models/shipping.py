from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ShippingLabel(Base):
    __tablename__ = "shipping_labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    length_in: Mapped[float] = mapped_column(Float, nullable=False)
    width_in: Mapped[float] = mapped_column(Float, nullable=False)
    height_in: Mapped[float] = mapped_column(Float, nullable=False)
    weight_oz: Mapped[float] = mapped_column(Float, nullable=False)
    label_fee: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    label_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
