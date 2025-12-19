"""Database models and connection"""
from sqlalchemy import event
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, List
import os

# Database connection - store in user's home directory for write access
DB_DIR = os.path.join(os.path.expanduser("~"), ".zara_stock_tracker")
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DB_DIR, "zara_stock.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# Database setup with better concurrency
engine = create_engine(
    DATABASE_URL,
    connect_args={'timeout': 30},  # Wait up to 30s instead of default 5s
    echo=False
)

# Enable WAL mode for better concurrency


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


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
    price_history = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan")


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


class PriceHistory(Base):
    """Price history for products"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    zara_product_id = Column(Integer, ForeignKey(
        "zara_products.id"), nullable=False)
    price = Column(Float, nullable=False)
    old_price = Column(Float)
    discount = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.now)

    product = relationship("ZaraProduct", back_populates="price_history")


class UserSettings(Base):
    """User settings storage"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get database session"""
    return SessionLocal()


def add_price_history(product_id: int, price: float, old_price: Optional[float] = None, discount: Optional[str] = None) -> None:
    """Add price history record (only if price changed)"""
    session = get_session()
    try:
        last_record = session.query(PriceHistory).filter(
            PriceHistory.zara_product_id == product_id
        ).order_by(PriceHistory.recorded_at.desc()).first()

        if not last_record or last_record.price != price:
            history = PriceHistory(
                zara_product_id=product_id,
                price=price,
                old_price=old_price,
                discount=discount
            )
            session.add(history)
            session.commit()
    finally:
        session.close()


def get_price_history(product_id: int, limit: int = 30) -> List[PriceHistory]:
    """Get price history for a product"""
    session = get_session()
    try:
        return session.query(PriceHistory).filter(
            PriceHistory.zara_product_id == product_id
        ).order_by(PriceHistory.recorded_at.desc()).limit(limit).all()
    finally:
        session.close()


def get_setting(key: str, default: str = "") -> str:
    """Get a user setting"""
    session = get_session()
    try:
        setting = session.query(UserSettings).filter(
            UserSettings.setting_key == key).first()
        return setting.setting_value if setting else default
    finally:
        session.close()


def set_setting(key: str, value: str) -> None:
    """Set a user setting"""
    session = get_session()
    try:
        setting = session.query(UserSettings).filter(
            UserSettings.setting_key == key).first()
        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.now()
        else:
            setting = UserSettings(setting_key=key, setting_value=value)
            session.add(setting)
        session.commit()
    finally:
        session.close()
