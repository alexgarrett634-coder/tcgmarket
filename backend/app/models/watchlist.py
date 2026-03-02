from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    preferred_source: Mapped[str] = mapped_column(String(30), default="tcgplayer")
    alert_above: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_below: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="watchlist_items")
    card: Mapped["Card | None"] = relationship("Card")
    product: Mapped["SealedProduct | None"] = relationship("SealedProduct")
    price_alerts: Mapped[list["PriceAlert"]] = relationship("PriceAlert", back_populates="watchlist_item")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlist.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    triggered_price: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_price: Mapped[float] = mapped_column(Float, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    seen: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    watchlist_item: Mapped["WatchlistItem"] = relationship("WatchlistItem", back_populates="price_alerts")
