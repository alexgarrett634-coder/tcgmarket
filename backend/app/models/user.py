from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False)
    seller_profile: Mapped["SellerProfile"] = relationship("SellerProfile", back_populates="user", uselist=False)
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship("WatchlistItem", back_populates="user")
    portfolio_items: Mapped[list["PortfolioItem"]] = relationship("PortfolioItem", back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
