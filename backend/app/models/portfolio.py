from datetime import datetime, date
from sqlalchemy import String, Float, Boolean, DateTime, Date, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    card_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("cards.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sealed_products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    condition: Mapped[str] = mapped_column(String(10), default="NM")
    purchase_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    preferred_source: Mapped[str] = mapped_column(String(30), default="tcgplayer")
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="portfolio_items")
    card: Mapped["Card | None"] = relationship("Card")
    product: Mapped["SealedProduct | None"] = relationship("SealedProduct")
