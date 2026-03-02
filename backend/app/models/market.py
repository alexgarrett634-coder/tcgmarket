from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PredictionMarket(Base):
    __tablename__ = "prediction_markets"
    __table_args__ = (
        Index("idx_markets_status", "status", "target_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    market_type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="coins", nullable=False)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    resolved_outcome: Mapped[str | None] = mapped_column(String(5), nullable=True)
    resolved_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pool_yes: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    pool_no: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    total_volume: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger_signal: Mapped[str | None] = mapped_column(String(50), nullable=True)

    card: Mapped["Card | None"] = relationship("Card")
    product: Mapped["SealedProduct | None"] = relationship("SealedProduct")
    positions: Mapped[list["MarketPosition"]] = relationship("MarketPosition", back_populates="market")


class MarketPosition(Base):
    __tablename__ = "market_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    market_id: Mapped[int] = mapped_column(ForeignKey("prediction_markets.id"), nullable=False)
    side: Mapped[str] = mapped_column(String(5), nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    settled: Mapped[bool] = mapped_column(Boolean, default=False)
    payout: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User")
    market: Mapped["PredictionMarket"] = relationship("PredictionMarket", back_populates="positions")
