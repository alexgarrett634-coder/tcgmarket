from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, Integer, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="subscription")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")


class UsageTracking(Base):
    __tablename__ = "usage_tracking"
    __table_args__ = (UniqueConstraint("user_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
