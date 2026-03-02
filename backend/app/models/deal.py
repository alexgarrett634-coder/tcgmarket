from datetime import datetime
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DealListing(Base):
    __tablename__ = "deal_listings"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        Index("idx_deals_score", "deal_score", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    listing_url: Mapped[str] = mapped_column(String(500), nullable=False)
    listed_price: Mapped[float] = mapped_column(Float, nullable=False)
    market_price: Mapped[float] = mapped_column(Float, nullable=False)
    deal_score: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seller: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    card: Mapped["Card | None"] = relationship("Card")
    product: Mapped["SealedProduct | None"] = relationship("SealedProduct")


class DealAlert(Base):
    __tablename__ = "deal_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    min_deal_score: Mapped[float] = mapped_column(Float, default=10.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
    card: Mapped["Card | None"] = relationship("Card")
    product: Mapped["SealedProduct | None"] = relationship("SealedProduct")
