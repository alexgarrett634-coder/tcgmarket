from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CardPrice(Base):
    __tablename__ = "card_prices"
    __table_args__ = (
        Index("idx_card_prices_lookup", "card_id", "source", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    card_id: Mapped[str] = mapped_column(String(100), ForeignKey("cards.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    price_type: Mapped[str] = mapped_column(String(30), nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    card: Mapped["Card"] = relationship("Card", back_populates="prices")


class ProductPrice(Base):
    __tablename__ = "product_prices"
    __table_args__ = (
        Index("idx_product_prices_lookup", "product_id", "source", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("sealed_products.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    price_type: Mapped[str] = mapped_column(String(30), nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["SealedProduct"] = relationship("SealedProduct", back_populates="prices")


class PriceFetchLog(Base):
    __tablename__ = "price_fetch_log"

    item_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source: Mapped[str] = mapped_column(String(30), primary_key=True)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(20), default="ok")
