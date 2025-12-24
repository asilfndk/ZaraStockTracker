"""
Database models for Zara Stock Tracker

SQLAlchemy ORM models for products, stock status, price history, and settings.
"""
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ZaraProduct(Base):
    """Product being tracked."""

    __tablename__ = "zara_products"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False)
    product_name = Column(String(300))
    product_id = Column(String(50))
    price = Column(Float, default=0.0)
    old_price = Column(Float, default=0.0)
    discount = Column(String(20))
    color = Column(String(100))
    image_url = Column(String(500))
    desired_size = Column(String(20))
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    last_check = Column(DateTime)

    stock_statuses = relationship(
        "ZaraStockStatus",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    price_history = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ZaraProduct(id={self.id}, name='{self.product_name}')>"


class ZaraStockStatus(Base):
    """Stock status for a product size."""

    __tablename__ = "zara_stock_statuses"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(
        Integer,
        ForeignKey("zara_products.id"),
        nullable=False
    )
    size = Column(String(20), nullable=False)
    in_stock = Column(Integer, default=0)
    stock_status = Column(String(50))
    last_updated = Column(DateTime, default=datetime.now)

    product = relationship(
        "ZaraProduct",
        back_populates="stock_statuses"
    )

    def __repr__(self):
        status = "in_stock" if self.in_stock else "out_of_stock"
        return f"<ZaraStockStatus(size='{self.size}', status='{status}')>"


class PriceHistory(Base):
    """Price history record for a product."""

    __tablename__ = "price_history"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(
        Integer,
        ForeignKey("zara_products.id"),
        nullable=False
    )
    price = Column(Float, nullable=False)
    old_price = Column(Float)
    discount = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.now)

    product = relationship(
        "ZaraProduct",
        back_populates="price_history"
    )

    def __repr__(self):
        return f"<PriceHistory(price={self.price}, recorded_at={self.recorded_at})>"


class UserSettings(Base):
    """User settings key-value storage."""

    __tablename__ = "user_settings"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(500), nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __repr__(self):
        return f"<UserSettings(key='{self.setting_key}')>"
