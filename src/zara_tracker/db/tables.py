"""SQLAlchemy table definitions."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ProductTable(Base):
    """Products being tracked."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    product_name = Column(String(300), nullable=False)
    product_id = Column(String(50))
    price = Column(Float, default=0.0)
    old_price = Column(Float, default=0.0)
    discount = Column(String(20), default="")
    color = Column(String(100), default="")
    image_url = Column(String(500), default="")
    desired_size = Column(String(20))
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    last_check = Column(DateTime)

    # Relationships
    stock_statuses = relationship(
        "StockStatusTable",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    price_history = relationship(
        "PriceHistoryTable",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.product_name[:30]}...')>"


class StockStatusTable(Base):
    """Stock status for product sizes."""

    __tablename__ = "stock_statuses"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(
        "products.id", ondelete="CASCADE"), nullable=False, index=True)
    size = Column(String(30), nullable=False)
    in_stock = Column(Boolean, default=False)
    stock_status = Column(String(30), default="out_of_stock")
    last_updated = Column(DateTime, default=datetime.now,
                          onupdate=datetime.now)

    # Relationship
    product = relationship("ProductTable", back_populates="stock_statuses")

    def __repr__(self):
        status = "✓" if self.in_stock else "✗"
        return f"<Stock({self.size}: {status})>"


class PriceHistoryTable(Base):
    """Price history records."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(
        "products.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    old_price = Column(Float, default=0.0)
    discount = Column(String(20), default="")
    recorded_at = Column(DateTime, default=datetime.now, index=True)

    # Relationship
    product = relationship("ProductTable", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(price={self.price}, at={self.recorded_at})>"


class SettingsTable(Base):
    """User settings storage."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Setting({self.key}={self.value[:20]})>"
