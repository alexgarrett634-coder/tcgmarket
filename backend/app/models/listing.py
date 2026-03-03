from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    stripe_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="seller_profile")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'card' or 'sealed'
    card_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)  # NM, LP, MP, HP, DMG
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, sold, cancelled
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # PSA/BGS grade: 6-10; None = raw/ungraded
    grading_company: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # 'PSA', 'BGS', etc.
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Seller-uploaded product photo
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
    card: Mapped[Optional["Card"]] = relationship("Card")
    product: Mapped[Optional["SealedProduct"]] = relationship("SealedProduct")
