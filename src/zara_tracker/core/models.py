"""
Database models for Zara Stock Tracker

SQLAlchemy ORM models for products, stock status, price history, and settings.
"""
from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ZaraProduct(Base):
    """Product being tracked."""

    __tablename__ = "zara_products"

    id: int = Column(Integer, primary_key=True, index=True)
    url: str = Column(String(500), unique=True, nullable=False)
    product_name: str = Column(String(300))
    product_id: str = Column(String(50))
    price: float = Column(Float, default=0.0)
    old_price: float = Column(Float, default=0.0)
    discount: str = Column(String(20))
    color: str = Column(String(100))
    image_url: str = Column(String(500))
    desired_size: str = Column(String(20))
    active: int = Column(Integer, default=1)
    created_at: datetime = Column(DateTime, default=datetime.now)
    last_check: datetime = Column(DateTime)

    stock_statuses: List["ZaraStockStatus"] = relationship(
        "ZaraStockStatus",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    price_history: List["PriceHistory"] = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ZaraProduct(id={self.id}, name='{self.product_name}')>"


class ZaraStockStatus(Base):
    """Stock status for a product size."""

    __tablename__ = "zara_stock_statuses"

    id: int = Column(Integer, primary_key=True, index=True)
    zara_product_id: int = Column(
        Integer,
        ForeignKey("zara_products.id"),
        nullable=False
    )
    size: str = Column(String(20), nullable=False)
    in_stock: int = Column(Integer, default=0)
    stock_status: str = Column(String(50))
    last_updated: datetime = Column(DateTime, default=datetime.now)

    product: "ZaraProduct" = relationship(
        "ZaraProduct",
        back_populates="stock_statuses"
    )

    def __repr__(self) -> str:
        status = "in_stock" if self.in_stock else "out_of_stock"
        return f"<ZaraStockStatus(size='{self.size}', status='{status}')>"


class PriceHistory(Base):
    """Price history record for a product."""

    __tablename__ = "price_history"

    id: int = Column(Integer, primary_key=True, index=True)
    zara_product_id: int = Column(
        Integer,
        ForeignKey("zara_products.id"),
        nullable=False
    )
    price: float = Column(Float, nullable=False)
    old_price: float = Column(Float)
    discount: str = Column(String(20))
    recorded_at: datetime = Column(DateTime, default=datetime.now)

    product: "ZaraProduct" = relationship(
        "ZaraProduct",
        back_populates="price_history"
    )

    def __repr__(self) -> str:
        return f"<PriceHistory(price={self.price}, recorded_at={self.recorded_at})>"


class UserSettings(Base):
    """User settings key-value storage."""

    __tablename__ = "user_settings"

    id: int = Column(Integer, primary_key=True, index=True)
    setting_key: str = Column(String(100), unique=True, nullable=False)
    setting_value: str = Column(String(500), nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __repr__(self) -> str:
        return f"<UserSettings(key='{self.setting_key}')>"
