from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    set_name: Mapped[str] = mapped_column(String(255), nullable=False)
    set_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rarity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supertype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subtypes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_small: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_large: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en", index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    prices: Mapped[list["CardPrice"]] = relationship("CardPrice", back_populates="card")
