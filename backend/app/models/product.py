from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SealedProduct(Base):
    __tablename__ = "sealed_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    set_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pricecharting_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ebay_search_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prices: Mapped[list["ProductPrice"]] = relationship("ProductPrice", back_populates="product")
