"""Database models and connection"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database connection
DATABASE_URL = "sqlite:///zara_stock.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ZaraProduct(Base):
    """Zara products being tracked"""
    __tablename__ = "zara_products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False)
    product_name = Column(String(300))
    product_id = Column(String(50))  # Zara's product ID
    price = Column(Float, default=0.0)
    old_price = Column(Float, default=0.0)  # Price before discount
    discount = Column(String(20))  # Discount percentage
    color = Column(String(100))
    image_url = Column(String(500))
    desired_size = Column(String(20))  # Size user wants to track
    active = Column(Integer, default=1)  # Is tracking active?
    created_at = Column(DateTime, default=datetime.now)
    last_check = Column(DateTime)

    stock_statuses = relationship(
        "ZaraStockStatus", back_populates="product", cascade="all, delete-orphan")


class ZaraStockStatus(Base):
    """Zara product size stock statuses"""
    __tablename__ = "zara_stock_statuses"

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(Integer, ForeignKey(
        "zara_products.id"), nullable=False)
    size = Column(String(20), nullable=False)
    in_stock = Column(Integer, default=0)  # 1: yes, 0: no
    stock_status = Column(String(50))  # in_stock, out_of_stock, low_on_stock
    last_updated = Column(DateTime, default=datetime.now)

    product = relationship("ZaraProduct", back_populates="stock_statuses")


def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get database session"""
    return SessionLocal()
